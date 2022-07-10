import argparse

from . import config, twitch, peertube
from .game_lookup import search


def add_twitch(args: argparse.Namespace) -> None:
    cfg = config.get()
    name = f"config.{args.NAME}"
    if name in cfg:
        raise ValueError(f"There's already a service named \"{args.NAME}\"")
    cfg[name] = {}
    cfg[name]["type"] = "twitch"
    cfg[name]["client_id"] = args.CLIENT_ID
    cfg[name]["client_secret"] = args.CLIENT_SECRET
    cfg[name]["enabled"] = "1"
    config.set(cfg)
    print(f"Added \"{args.NAME}\" as a Twitch service")


def add_peertube(args: argparse.Namespace) -> None:
    cfg = config.get()
    name = f"config.{args.NAME}"
    if name in cfg:
        raise ValueError(f"There's already a service named \"{args.NAME}\"")
    cfg[name] = {}
    cfg[name]["type"] = "peertube"
    cfg[name]["base_url"] = args.BASE_URL
    cfg[name]["username"] = args.USERNAME
    cfg[name]["password"] = args.PASSWORD
    cfg[name]["enabled"] = "1"
    config.set(cfg)
    print(f"Added \"{args.NAME}\" as a PeerTube service")


def create(args: argparse.Namespace):
    cfg = config.get()
    for key in cfg.keys():
        if key.startswith("config."):
            svc_name = key[7:]
            if cfg[key]["enabled"] != "1":
                continue
            print(f"Creating stream on {svc_name}...")
            if cfg[key]["type"] == "twitch":
                twitch.create_stream(
                    svc_name,
                    title=args.title,
                    description=args.description,
                    announcement=args.announcement,
                    game=args.game,
                    gameid=args.gameid,
                    lang=args.lang,
                    vod=args.vod
                )
            elif cfg[key]["type"] == "peertube":
                peertube.create_stream(
                    svc_name,
                    title=args.title,
                    description=args.description,
                    announcement=args.announcement,
                    game=args.game,
                    gameid=args.gameid,
                    lang=args.lang,
                    vod=args.vod
                ) 

def update(args: argparse.Namespace):
    cfg = config.get()


def set_defaults(args: argparse.Namespace):
    cfg = config.get()
    if "defaults" not in cfg:
        cfg["defaults"] = {
            "title": None,
            "description": None,
            "announcement": None,
            "game": None,
            "gameid": None,
            "lang": None,
            "vod": "1",
        }
   
    if args.title is not None:
        cfg["defaults"]["title"] = args.title

    if args.description is not None:
        cfg["defaults"]["description"] = args.description

    if args.announcement is not None:
        cfg["defaults"]["announcement"] = args.announcement
    
    if args.game is not None:
        cfg["defaults"]["game"] = args.game
    
    if args.gameid is not None:
        cfg["defaults"]["gameid"] = args.gameid

    if args.lang is not None:
        cfg["defaults"]["lang"] = args.lang

    cfg["defaults"]["vod"] = "1" if args.vod else "0"


def enable(args: argparse.Namespace) -> None:
    cfg = config.get()
    name = f"config.{args.NAME}"
    if name not in cfg:
        raise ValueError(f"No service named \"{args.NAME}\"")
    cfg[name]["enabled"] = "1"
    config.set(cfg)


def disable(args: argparse.Namespace) -> None:
    cfg = config.get()
    name = f"config.{args.NAME}"
    if name not in cfg:
        raise ValueError(f"No service named \"{args.NAME}\"")
    cfg[name]["enabled"] = "0"
    config.set(cfg)


def game_lookup(args: argparse.Namespace) -> None:
    results = search(args.NAME)
    for r in results:
        print(f"{r.name} (id {r.game_id}, confidence {r.confidence})")


def main():
    parser = argparse.ArgumentParser(
        description="Manage streaming across multiple services",
    )
    subparser = parser.add_subparsers()

    parser_add = subparser.add_parser("add", description="Add a streaming service")
    parser_add_subs = parser_add.add_subparsers()
    parser_add_twitch = parser_add_subs.add_parser("twitch", description="Add a Twitch account", epilog="""To get these parameters, log into https://dev.twitch.tv/console and add a new application for mrstream. You'll need to set the OAuth redirect URL to http://localhost and the Category to Broadcaster Suite.""")
    parser_add_twitch.add_argument("NAME", help="Local name for service")
    parser_add_twitch.add_argument("CLIENT_ID", help="OAuth client ID")
    parser_add_twitch.add_argument("CLIENT_SECRET", help="OAuth client secret")
    parser_add_twitch.set_defaults(func=add_twitch)

    parser_add_peertube = parser_add_subs.add_parser("peertube", description="Add an account on a PeerTube instance")
    parser_add_peertube.add_argument("NAME", help="Local name for service")
    parser_add_peertube.add_argument("BASE_URL", help="Top-level URL of the PeerTube instance")
    parser_add_peertube.add_argument("USERNAME", help="Account username")
    parser_add_peertube.add_argument("PASSWORD", help="Account password")
    parser_add_peertube.set_defaults(func=add_peertube)
    
    parser_enable = subparser.add_parser("enable", description="Enable a streaming account")
    parser_enable.add_argument("NAME", help="Local name for service")
    parser_enable.set_defaults(func=enable)

    parser_disable = subparser.add_parser("disable", description="Disable a streaming account")
    parser_disable.add_argument("NAME", help="Local name for service")
    parser_disable.set_defaults(func=disable)

    parser_game_lookup = subparser.add_parser("game_lookup", description="Search the Twitch game list")
    parser_game_lookup.add_argument("NAME", help="Name to search for")
    parser_game_lookup.set_defaults(func=game_lookup)

    parser_create = subparser.add_parser("create", description="Initialise a new streaming session")
    parser_create.add_argument("--title", help="Title of the stream")
    parser_create.add_argument("--description", help="Description of the stream")
    parser_create.add_argument("--announcement", help="Announcement message for the stream")
    parser_create.add_argument("--game", help="Game being played")
    parser_create.add_argument("--gameid", help="Twitch ID of game being played")
    parser_create.add_argument("--lang", help="ISO 639-1 code for the stream language")
    parser_create.add_argument("--novod", dest='vod', action='store_false', help="Disable recording")
    parser_create.set_defaults(func=create)

    parser_update = subparser.add_parser("update", description="Update streaming session in progress")
    parser_update.add_argument("--title", help="Title of the stream")
    parser_update.add_argument("--description", help="Description of the stream")
    parser_update.add_argument("--announcement", help="Announcement message for the stream")
    parser_update.add_argument("--game", help="Game being played")
    parser_update.add_argument("--gameid", help="Twitch ID of game being played")
    parser_update.add_argument("--lang", help="ISO 639-1 code for the stream language")
    parser_update.add_argument("--novod", dest='vod', action='store_false', help="Disable recording")
    parser_update.set_defaults(func=update)
     
    parser_set_defaults = subparser.add_parser("set_defaults", description="Set the defaults for a streaming session")
    parser_set_defaults.add_argument("--title", help="Title of the stream")
    parser_set_defaults.add_argument("--description", help="Description of the stream")
    parser_set_defaults.add_argument("--announcement", help="Announcement message for the stream")
    parser_set_defaults.add_argument("--game", help="Game being played")
    parser_set_defaults.add_argument("--gameid", help="Twitch ID of game being played")
    parser_set_defaults.add_argument("--lang", help="ISO 639-1 code for the stream language")
    parser_set_defaults.add_argument("--novod", dest='vod', action='store_false', help="Disable recording")
    parser_set_defaults.set_defaults(func=set_defaults)


    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
