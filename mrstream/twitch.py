import asyncio
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncContextManager, AsyncIterator, Awaitable, Callable, List, Optional
from typing_extensions import NamedTuple
from websockets import server as websocket_server
from websockets.exceptions import WebSocketException 
import requests
import json

from twitchAPI.chat import Chat, ChatEvent, ChatMessage
from twitchAPI.object.api import SearchCategoryResult, Video
from twitchAPI.object.eventsub import ChannelChatMessageEvent, ChannelFollowEvent, ChannelRaidEvent
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, VideoType
from twitchAPI.oauth import UserAuthenticator, validate_token, refresh_access_token
from twitchAPI.eventsub.websocket import EventSubWebsocket
from websockets.typing import Data

from . import config


TWITCH_SCOPES = [
    AuthScope.CHANNEL_READ_STREAM_KEY,
    AuthScope.CHANNEL_MANAGE_BROADCAST,
    AuthScope.USER_READ_EMAIL,
    AuthScope.USER_EDIT,
    AuthScope.USER_EDIT_BROADCAST,
    AuthScope.MODERATOR_READ_FOLLOWERS,
    AuthScope.USER_READ_CHAT,
    AuthScope.USER_WRITE_CHAT,
    AuthScope.CHANNEL_BOT,
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
        if "refresh_token" in sub and sub["refresh_token"].strip():
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
async def get_eventsub_websocket(tw: Twitch) -> AsyncIterator[EventSubWebsocket]:
    eventsub = EventSubWebsocket(tw)
    eventsub.start()
    try:
        yield eventsub
    finally:
        await eventsub.stop()
        await tw.close()



EVENT_BUS: dict[tuple, asyncio.Queue[str]] = {}

async def eventsub_handler(client_response: Callable[[str], Awaitable[None]], ws: websocket_server.WebSocketServerProtocol) -> None:
    print(f"Client joined - {ws.remote_address}")
    EVENT_BUS[ws.remote_address] = asyncio.Queue()
    try:
        while not ws.closed:
            try:
                data = EVENT_BUS[ws.remote_address].get_nowait()
                await ws.send(data)
            except asyncio.QueueEmpty:
                pass

            try:
                data: str = await asyncio.wait_for(ws.recv(), 0.1) # type: ignore
                await client_response(data)
            except (WebSocketException, asyncio.TimeoutError):
                pass

    finally:
        print(f"Client quit - {ws.remote_address}")


async def run_eventsub_server(name: str, port: int=26661) -> None:
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    tw = await get_client(name)

    async def event_raid(ev: ChannelRaidEvent) -> None:
        print(f"RAID - {ev.event.from_broadcaster_user_name}, {ev.event.viewers} souls")
        for queue in EVENT_BUS.values():
            await queue.put(json.dumps({
                "type": "raid",
                "username": ev.event.from_broadcaster_user_name,
                "viewers": ev.event.viewers,
            }))

    async def event_follow(ev: ChannelFollowEvent) -> None:
        print(f"FOLLOW - {ev.event.user_name}")
        for queue in EVENT_BUS.values():
            await queue.put(json.dumps({
                "type": "follow",
                "username": ev.event.user_name,
            }))

    async def event_chat_message(ev: ChannelChatMessageEvent) -> None:
        print(f"CHAT MESSAGE - {ev.event.message_id} <{ev.event.chatter_user_name}> {ev.event.message.text}")
        for queue in EVENT_BUS.values():
            await queue.put(json.dumps({
                "type": "message",
                "username": ev.event.chatter_user_name,
                "text": ev.event.message.text,
                "id": ev.event.message_id,
            }))


    async def handle_client_response(message: Data) -> None:
        data = json.loads(message)
        if isinstance(data, dict):
            if data.get("type") == "message":
                await tw.send_chat_message(sub.get("user_id"), sub.get("user_id"), data.get("text", ""), data.get("reply_id"))
                return
        print(f"Unknown data: {message}")
    

    async with get_eventsub_websocket(tw) as eventsub:
        await eventsub.listen_channel_follow_v2(sub.get("user_id"), sub.get("user_id"), event_follow)
        await eventsub.listen_channel_raid(event_raid, sub.get("user_id"), None)
        await eventsub.listen_channel_chat_message(sub.get("user_id"), sub.get("user_id"), event_chat_message)
        async with websocket_server.serve(partial(eventsub_handler, handle_client_response), "", port):
            print(f"Websocket server running on ws://localhost:{port}")
            await asyncio.Future()


