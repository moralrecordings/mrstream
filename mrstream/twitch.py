from typing import List, Optional
import requests
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
from twitchAPI.oauth import UserAuthenticator, validate_token, refresh_access_token

from . import config

TWITCH_SCOPES = [
    AuthScope.CHANNEL_READ_STREAM_KEY,
    AuthScope.CHANNEL_MANAGE_BROADCAST,
    AuthScope.USER_READ_EMAIL,
    AuthScope.USER_EDIT,
    AuthScope.USER_EDIT_BROADCAST,
]

def authenticate(name: str) -> None:
    cfg = config.get()
    sub = cfg[f"config.{name}"]

    client_id: str = sub.get("client_id")
    client_secret: str = sub.get("client_secret")
    
    if "token" in sub:
        validation = validate_token(sub["token"])
        if "user_id" in validation:
            return
        if "refresh_token" in sub:
            token, refresh_token = refresh_access_token(sub["refresh_token"], client_id, client_secret)
            sub["token"] = token
            sub["refresh_token"] = refresh_token
            config.set(cfg)
            return
    
    tw = Twitch(client_id, client_secret)

    ua = UserAuthenticator(tw, TWITCH_SCOPES)
    auth_result = ua.authenticate()
    if auth_result is None:
        raise RuntimeError("User authentication failed")

    sub["token"] = auth_result[0]
    sub["refresh_token"] = auth_result[1]

    # Run the validator again
    validation = validate_token(sub["token"])
    if "user_id" not in validation:
        raise RuntimeError("Validation of authenticated token failed")

    sub["login"] = validation["login"]
    sub["user_id"] = validation["user_id"]

    config.set(cfg)


def get_client(name: str) -> Twitch:
    authenticate(name)

    cfg = config.get()
    sub = cfg[f"config.{name}"]
    client_id: str = sub.get("client_id")
    client_secret: str = sub.get("client_secret")
    token: str = sub.get("token")
    refresh_token: str = sub.get("refresh_token")
    tw = Twitch(client_id, client_secret)
    tw.set_user_authentication(token, TWITCH_SCOPES, refresh_token)
    return tw


def create_stream(
    name: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    announcement: Optional[str] = None,
    game: Optional[str] = None,
    gameid: Optional[str] = None,
    lang: Optional[str] = None,
    vod: bool = False
) -> None:
    tw = get_client(name)
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    sub["stream_key"] = tw.get_stream_key(sub.get("user_id"))["data"][0]["stream_key"]
    if game is not None and gameid is None:
        game_lookups = tw.search_categories(game)["data"]
        if game_lookups:
            gameid = game_lookups[0]["id"]
    tw.modify_channel_information(sub["user_id"], game_id = gameid, broadcaster_language=lang, title=title)

    ingest = requests.get("https://ingest.twitch.tv/ingests").json()["ingests"][0]["url_template"]
    sub["endpoint"] = ingest.format(stream_key=sub["stream_key"])

    print(f"{name}: https://twitch.tv/{sub['login']}")

    config.set(cfg)


