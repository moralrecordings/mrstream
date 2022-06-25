import argparse
from streamctl import config


def add_twitch(args: argparse.Namespace):
    cfg = config.get()
    if args.NAME in cfg:
        raise ValueError(f"There's already a service named \"{args.NAME}\"")
    cfg[args.NAME] = {}
    cfg[args.NAME]["type"] = "twitch"
    cfg[args.NAME]["client_id"] = args.CLIENT_ID
    cfg[args.NAME]["client_secret"] = args.CLIENT_SECRET
    config.set(cfg)
    print(f"Added \"{args.NAME}\" as a Twitch service")


def add_peertube(args: argparse.Namespace):
    cfg = config.get()
    if args.NAME in cfg:
        raise ValueError(f"There's already a service named \"{args.NAME}\"")
    cfg[args.NAME] = {}
    cfg[args.NAME]["type"] = "peertube"
    cfg[args.NAME]["base_url"] = args.BASE_URL
    cfg[args.NAME]["username"] = args.USERNAME
    cfg[args.NAME]["password"] = args.PASSWORD
    config.set(cfg)
    print(f"Added \"{args.NAME}\" as a PeerTube service")


def create(args: argparse.Namespace):
    cfg = config.get()
    


def main():
    parser = argparse.ArgumentParser(
        description="Manage streaming across multiple services",
    )
    subparser = parser.add_subparsers()

    parser_add = subparser.add_parser("add", description="Add a streaming service")
    parser_add_subs = parser_add.add_subparsers()
    parser_add_twitch = parser_add_subs.add_parser("twitch", description="Add a Twitch account", epilog="""To get these parameters, log into https://dev.twitch.tv/console and add a new application for streamctl. You'll need to set the OAuth redirect URL to http://localhost and the Category to Broadcaster Suite.""")
    parser_add_twitch.add_argument("NAME", help="Local name for service")
    parser_add_twitch.add_argument("CLIENT_ID", help="OAuth client ID")
    parser_add_twitch.add_argument("CLIENT_SECRET", help="OAuth client secret")
    parser_add_twitch.set_defaults(func=add_twitch)

    parser_add_peertube = parser_add_subs.add_parser("peertube", description="Add an account on a PeerTube instance", epilog="""To get these parameters, log in to the PeerTube instance and visit /api/v1/oauth-clients/local
    """)
    parser_add_peertube.add_argument("NAME", help="Local name for service")
    parser_add_peertube.add_argument("BASE_URL", help="Top-level URL of the PeerTube instance")
    parser_add_peertube.add_argument("CLIENT_ID", help="OAuth client ID")
    parser_add_peertube.add_argument("CLIENT_SECRET", help="OAuth client secret")
    parser_add_twitch.set_defaults(func=add_peertube)
    
    parser_create = subparser.add_parser("init", description="Initialise a new streaming session")
    parser_create.add_argument("TITLE", help="Title of the stream")
    parser_create.add_argument("--description", help="Description of the stream")
    parser_create.add_argument("--announcement", help="Announcement message for the stream")
    parser_create.add_argument("--tags", help="Tags to add to the video")
    parser_create.set_defaults(func=create)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
