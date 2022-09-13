from typing import Optional
import requests

from . import config


def authenticate(name: str) -> None:
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    
    if "client_id" not in sub:
        clients = requests.get(f"{sub['base_url']}/api/v1/oauth-clients/local").json()
        sub["client_id"] = clients["client_id"]
        sub["client_secret"] = clients["client_secret"]

    if "refresh_token" in sub:
        response = requests.post(
            f"{sub['base_url']}/api/v1/users/token",
            {
                "grant_type": "refresh_token",
                "client_id": sub["client_id"],
                "client_secret": sub["client_secret"],
                "refresh_token": sub["refresh_token"],
            },
        )
        if response.status_code == 200:
            rj = response.json()
            sub["token"] = rj["access_token"]
            sub["refresh_token"] = rj["refresh_token"]
            config.set(cfg)
            return
 
    response = requests.post(
        f"{sub['base_url']}/api/v1/users/token",
        {
            "grant_type": "password",
            "client_id": sub["client_id"],
            "client_secret": sub["client_secret"],
            "username": sub["username"],
            "password": sub["password"],
        },
    )
    response.raise_for_status()
    rj = response.json()
    sub["token"] = rj["access_token"]
    sub["refresh_token"] = rj["refresh_token"]

    user = requests.get(f"{sub['base_url']}/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {sub['token']}"
        }
    ).json()

    sub["channel_id"] = str(user["videoChannels"][0]["id"])

    config.set(cfg)


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
    authenticate(name)
    cfg = config.get()
    sub = cfg[f"config.{name}"]
    headers={
        "Authorization": f"Bearer {sub['token']}"
    }

    payload = {
        "channelId": sub["channel_id"], 
        "name": title,
        "saveReplay": vod,
        "privacy": 1,
    }
    if description:
        payload["description"] = description

    if lang:
        payload["language"] = lang

    response = requests.post(
        f"{sub['base_url']}/api/v1/videos/live",
        payload,
        headers=headers
    )
    response.raise_for_status()
    video_data = response.json()["video"]
    print(f"{name}: {sub['base_url']}/w/{video_data['shortUUID']}")

    sub["current_live_id"] = video_data["uuid"]

    endpoint = requests.get(
        f"{sub['base_url']}/api/v1/videos/live/{sub['current_live_id']}",
        headers=headers
    ).json()

    sub["stream_key"] = endpoint["streamKey"]
    sub["endpoint"] = endpoint["rtmpUrl"] + f"/{sub['stream_key']}"

    config.set(cfg)
    

