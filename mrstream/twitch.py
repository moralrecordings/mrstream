import asyncio
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncContextManager, AsyncIterator, Awaitable, Callable, List, Optional
from typing_extensions import NamedTuple
from websockets import server as websocket_server
import requests
import json

from twitchAPI.object.api import SearchCategoryResult, Video
from twitchAPI.object.eventsub import ChannelFollowEvent, ChannelRaidEvent
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, VideoType
from twitchAPI.oauth import UserAuthenticator, validate_token, refresh_access_token
from twitchAPI.eventsub.websocket import EventSubWebsocket

from . import config


TWITCH_SCOPES = [
    AuthScope.CHANNEL_READ_STREAM_KEY,
    AuthScope.CHANNEL_MANAGE_BROADCAST,
    AuthScope.USER_READ_EMAIL,
    AuthScope.USER_EDIT,
    AuthScope.USER_EDIT_BROADCAST,
    AuthScope.MODERATOR_READ_FOLLOWERS,
]


async def authenticate(name: str) -> None:
    cfg = config.get()
    sub = cfg[f"config.{name}"]

    client_id: str = sub.get("client_id")
    client_secret: str = sub.get("client_secret")

    if "token" in sub:
        validation = await validate_token(sub["token"])
        if "user_id" in validation:
            return
        if "refresh_token" in sub:
            token, refresh_token = await refresh_access_token(
                sub["refresh_token"], client_id, client_secret
            )
            sub["token"] = token
            sub["refresh_token"] = refresh_token
            config.set(cfg)
            return

    tw = Twitch(client_id, client_secret)

    ua = UserAuthenticator(tw, TWITCH_SCOPES)
    auth_result = await ua.authenticate()
    if auth_result is None:
        raise RuntimeError("User authentication failed")

    sub["token"] = auth_result[0]
    sub["refresh_token"] = auth_result[1]

    # Run the validator again
    validation = await validate_token(sub["token"])
    if "user_id" not in validation:
        raise RuntimeError("Validation of authenticated token failed")

    sub["login"] = validation["login"]
    sub["user_id"] = validation["user_id"]

    config.set(cfg)


async def get_client(name: str) -> Twitch:
    await authenticate(name)

    cfg = config.get()
    sub = cfg[f"config.{name}"]
    client_id: str = sub.get("client_id")
    client_secret: str = sub.get("client_secret")
    token: str = sub.get("token")
    refresh_token: str = sub.get("refresh_token")
    tw = Twitch(client_id, client_secret)
    await tw.set_user_authentication(token, TWITCH_SCOPES, refresh_token)
    return tw


async def search_games(name: str, title: str) -> list[SearchCategoryResult]:
    tw = await get_client(name)
    results = tw.search_categories(title)
    return [x async for x in results]


async def get_past_streams(name: str) -> list[Video]:
    tw = await get_client(name)
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    highlights = tw.get_videos(
        user_id=sub.get("user_id"), video_type=VideoType.HIGHLIGHT
    )
    return [x async for x in highlights]


async def create_stream(
    name: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    announcement: Optional[str] = None,
    game: Optional[str] = None,
    gameid: Optional[str] = None,
    lang: Optional[str] = None,
    vod: bool = False,
) -> None:
    tw = await get_client(name)
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    sub["stream_key"] = await tw.get_stream_key(sub.get("user_id"))
    if game is not None and gameid is None:
        game_lookups = [x async for x in tw.search_categories(game)]
        if game_lookups:
            gameid = game_lookups[0].id
    await tw.modify_channel_information(
        sub["user_id"], game_id=gameid, broadcaster_language=lang, title=title
    )

    ingest = requests.get("https://ingest.twitch.tv/ingests").json()["ingests"][0][
        "url_template"
    ]
    sub["endpoint"] = ingest.format(stream_key=sub["stream_key"])

    print(f"{name}: https://twitch.tv/{sub['login']}")

    config.set(cfg)


@asynccontextmanager
async def get_eventsub_websocket(name: str) -> AsyncIterator[EventSubWebsocket]:
    tw = await get_client(name)
    eventsub = EventSubWebsocket(tw)
    eventsub.start()
    try:
        yield eventsub
    finally:
        await eventsub.stop()
        await tw.close()


async def eventsub_handler(ws: websocket_server.WebSocketServerProtocol, name: str) -> None:
    print(f"Client joined - {ws.remote_address}")
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    async def event_raid(ev: ChannelRaidEvent) -> None:
        print(f"RAID - {ev.event.from_broadcaster_user_name}, {ev.event.viewers} souls")
        await ws.send(json.dumps({
            "type": "raid",
            "username": ev.event.from_broadcaster_user_name,
            "viewers": ev.event.viewers,
        }))

    async def event_follow(ev: ChannelFollowEvent) -> None:
        print(f"FOLLOW - {ev.event.user_name}")
        await ws.send(json.dumps({
            "type": "follow",
            "username": ev.event.user_name,
        }))

    async with get_eventsub_websocket(name) as eventsub:
        await eventsub.listen_channel_follow_v2(sub.get("user_id"), sub.get("user_id"), event_follow)
        await eventsub.listen_channel_raid(event_raid, None, sub.get("user_id"))
        try:
            await ws.wait_closed()
        finally:
            print(f"Client quit - {ws.remote_address}")
    

async def run_eventsub_server(name: str, port: int=26661) -> None:
    async with websocket_server.serve(partial(eventsub_handler, name=name), "", port):
        print(f"Websocket server running on ws://0.0.0.0:{port}")
        await asyncio.Future()


