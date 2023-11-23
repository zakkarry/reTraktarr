#!/usr/bin/env python3
""" main script, arguments and executions """
import sys
import argparse
from os import name, path, getenv

from retraktarr.api.arr import ArrAPI
from retraktarr.api.trakt import TraktAPI
from retraktarr.config import Configuration


def main():
    """main entry point defines args and processes stuff"""
    try:
        with open(
            path.join(path.dirname(path.abspath(__file__)), "VERSION"), encoding="utf-8"
        ) as f:
            VERSION = f.read()
    except OSError as e:
        VERSION = "MISSING"

    parser = argparse.ArgumentParser(
        description="Starr App -> Trakt.tv List Backup/Synchronization"
    )
    parser.add_argument(
        "--oauth",
        "-o",
        type=str,
        help="Update OAuth2 Bearer Token."
        " Accepts the auth code and requires valid Trakt "
        "config settings (ex: -o CODE_HERE)",
    )
    parser.add_argument(
        "--radarr",
        "-r",
        action="store_true",
        help="Synchronize Radarr movies with Trakt.tv",
    )
    parser.add_argument(
        "--sonarr",
        "-s",
        action="store_true",
        help="Synchronize Sonarr series with Trakt.tv",
    )
    parser.add_argument(
        "--all",
        "-all",
        "-a",
        action="store_true",
        help="Synchronize both Starr apps with Trakt.tv",
    )
    parser.add_argument(
        "--mon",
        "-m",
        action="store_true",
        help="Synchronize only monitored content with Trakt.tv",
    )
    parser.add_argument(
        "--qualityprofile",
        "-qp",
        type=str,
        help="The quality profile you wish to sync to Trakt.tv",
    )
    parser.add_argument(
        "--tag", "-t", type=str, help="The arr tag you wish to sync to Trakt.tv"
    )
    parser.add_argument(
        "--cat",
        "-c",
        action="store_true",
        help="Add to the Trakt.tv list without "
        "deletion (concatenate/append to list)",
    )
    parser.add_argument(
        "--list",
        "-l",
        type=str,
        help="Specifies the Trakt.tv list name. (overrides config file settings)",
    )
    parser.add_argument(
        "--wipe",
        "-w",
        action="store_true",
        help="Erases the associated list and performs a sync "
        "(requires -all or -r/s)",
    )
    parser.add_argument(
        "--privacy",
        "-p",
        type=str,
        help="Specifies the Trakt.tv list privacy settings "
        "(private/friends/public - overrides config file settings)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Forces a refresh_token exchange (oauth) "
        "and sets the config to a new tokens.",
    )
    parser.add_argument(
        "--timeout",
        type=str,
        help="Specifies the timeout in seconds to use for " "POST commands to Trakt.tv",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Displays current version information",
    )
    parser.add_argument(
        "--config",
        action="store",
        nargs="?",
        const=True,
        default=None,
        help="If a path is provided, retraktarr will use this config file, otherwise it outputs default config location.",
    )
    args = parser.parse_args()
    print(f"\nretraktarr v{VERSION}")
    if args.version:
        sys.exit(0)

    if args.config is not True and args.config is not None:
        config_path = args.config
    else:
        config_path = (
            f'{path.expanduser("~")}{path.sep}.config{path.sep}retraktarr.conf'
        )
        if args.config is True:
            print(f"Current default config file is {config_path}")
            exit(0)

    print(f"Validating Configuration File: {config_path}\n")
    config = Configuration(config_path)
    if args.oauth:
        config.get_oauth(args)
    if args.refresh:
        config.get_oauth(args)

    (
        oauth2_bearer,
        trakt_api_key,
        trakt_user,
        trakt_secret,
    ) = config.validate_trakt_credentials()
    trakt_api = TraktAPI(oauth2_bearer, trakt_api_key, trakt_user, trakt_secret)
    if args.list:
        trakt_api.list = args.list
    if args.privacy:
        trakt_api.list_privacy = args.privacy
    if args.timeout:
        trakt_api.post_timeout = args.timeout
    if args.radarr or args.all or args.sonarr:
        arr_api = ArrAPI()

    if args.radarr or args.all:
        config.validate_arr_configuration(arr_api, trakt_api, "Radarr", args)
        tvdb_ids, tmdb_ids, imdb_ids, trakt_ids = trakt_api.get_list(
            args, arr_api.endpoint["Radarr"][0]
        )
        arr_ids, arr_imdb, arr_data = arr_api.get_list(args, "Radarr")

        print("[Radarr]")
        trakt_api.add_to_list(
            args,
            arr_api.endpoint["Radarr"][2],
            arr_data,
            tmdb_ids,
            arr_api.endpoint["Radarr"][1],
            imdb_ids,
            arr_ids,
            arr_imdb,
            trakt_ids,
        )
        print(f"Total Movies: {len(arr_ids)}\n")

    if args.sonarr or args.all:
        config.validate_arr_configuration(arr_api, trakt_api, "Sonarr", args)
        tvdb_ids, tmdb_ids, imdb_ids, trakt_ids = trakt_api.get_list(
            args, arr_api.endpoint["Sonarr"][2].rstrip("s")
        )

        arr_ids, arr_imdb, arr_data = arr_api.get_list(args, "Sonarr")
        print("[Sonarr]")
        trakt_api.add_to_list(
            args,
            arr_api.endpoint["Sonarr"][2],
            arr_data,
            tvdb_ids,
            arr_api.endpoint["Sonarr"][1],
            imdb_ids,
            arr_ids,
            arr_imdb,
            trakt_ids,
        )
        print(f"Total Series: {len(arr_ids)}")
        sys.exit(1)

    if args.radarr or args.all:
        sys.exit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
