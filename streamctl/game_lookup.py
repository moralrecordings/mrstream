from typing import Dict, List, NamedTuple, Optional
import requests
from thefuzz import process

import csv
import os

from streamctl import config, twitch

TWITCH_GAME_LIST_SOURCE = "https://raw.githubusercontent.com/Nerothos/TwithGameList/master/game_info.csv"
TWITCH_GAME_LIST_PATH = os.path.join(config.LOCAL_CONFIG_DIR, "twitch_game_info.csv")

_TWITCH_GAME_ID_MAPPING: Dict[str, str] = {}
_TWITCH_GAME_NAMES: List[str] = []


class GameResult(NamedTuple):
    name: str
    game_id: str
    confidence: Optional[int]


def search(name: str) -> List[GameResult]:
    result = search_twitch(name)
    if not result:
        result = search_local(name)
    return result


def search_twitch(name: str) -> List[GameResult]:
    cfg = config.get()
    for k in cfg.keys():
        if k.startswith("config.") and cfg[k]["type"] == "twitch":
            svc_name = k[7:]
            client = twitch.get_client(svc_name)
            results = client.search_categories(name)
            return [GameResult(name=x["name"], game_id=x["id"], confidence=None) for x in results["data"]]
    return []


def search_local(name: str) -> List[GameResult]:
    # get the game list
    if not os.path.exists(TWITCH_GAME_LIST_PATH):
        twitch_list = requests.get(TWITCH_GAME_LIST_SOURCE)
        twitch_list.raise_for_status()
        with open(TWITCH_GAME_LIST_PATH, "wb") as output:
            output.write(twitch_list.content)
    
    if len(_TWITCH_GAME_ID_MAPPING) == 0:
        with open(TWITCH_GAME_LIST_PATH, "r") as listfile:
            c = csv.reader(listfile)
            next(c)
            for row in c:
                if len(row) > 2:
                    _TWITCH_GAME_ID_MAPPING[row[1]] = row[0]
        _TWITCH_GAME_NAMES.extend(_TWITCH_GAME_ID_MAPPING.keys())
    
    results = process.extract(name, _TWITCH_GAME_NAMES)
    return [GameResult(name=x[0], game_id=_TWITCH_GAME_ID_MAPPING[x[0]], confidence=x[1]) for x in results]
