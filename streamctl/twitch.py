import requests

import base64
import webbrowser
import uuid

import config

def authenticate_bad(name: str):
    cfg = config.get()
    sub = cfg[name]
    client_id: str = sub.get("client_id")
    client_secret: str = sub.get("client_secret")
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
    ).json()
    sub["access_token"] = response["access_token"]
    config.set(cfg)


def authenticate(name: str):
    cfg = config.get()
    sub = cfg[name]
    state = str(uuid.uuid4())
    connect_url = f"https://id.twitch.tv/oauth2/authorize?response_type=token&client_id={sub.get('client_id')}&redirect_uri=http://localhost:8000&state={state}"

    client_id: str = sub.get("client_id")
    client_secret: str = sub.get("client_secret")
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
    ).json()
    sub["access_token"] = response["access_token"]
    config.set(cfg)




def create_stream(name: str):
    cfg = config.get()
    sub = cfg[name]
    headers = {
        "Authorization": f"Bearer {base64.b64encode(sub['access_token'])}"
    }
    response = requests.post(
        "https://api.twitch.tv/helix/streams/key",
        data={
            "broadcaster_id": sub["broadcaster_id"],
        },
        headers=headers,
    )
