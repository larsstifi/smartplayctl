#!/usr/bin/env python3
import subprocess
import sys
import argparse
from pathlib import Path

def status():
    """
    Returns a dict of {player_name: status} using playerctl.
    Example: {"spotify": "Playing", "vlc": "Paused"}
    """
    players = []
    statuses = {}

    try:
        # List all running players
        result = subprocess.run(
            ["playerctl", "-l"], capture_output=True, text=True, check=True
        )
        players = [p.strip() for p in result.stdout.splitlines() if p.strip()]
    except subprocess.CalledProcessError:
        # No players running or playerctl not installed
        return {}

    for player in players:
        try:
            # Get playback status for each
            status = subprocess.run(
                ["playerctl", "-p", player, "status"],
                capture_output=True,
                text=True,
                check=True
            )
            statuses[player] = status.stdout.strip()
        except subprocess.CalledProcessError:
            # Player might have quit between listing and querying
            statuses[player] = "Unknown"

    return statuses

def remember_last_player(player):
    path = Path.home() / ".cache/smart-mediacontrol_last"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(player.strip())

def get_last_player():
    path = Path.home() / ".cache/smart-mediacontrol_last"
    if path.exists():
        return path.read_text().strip()
    return None

def select_player(args):

    if args.player:
        return args.player


    player_status = status()

    if not player_status:
        return None

    for p, st in player_status.items():
        if st.lower() == "playing":
            return p;
    
    last_player = get_last_player()

    if(last_player):
        return last_player

    return next(iter(player_status))


def main():
    parser = argparse.ArgumentParser(
        description="Smart wrapper around playerctl that decides which player(s) to control."
    )

    # Let’s mimic playerctl’s basic verbs
    parser.add_argument(
        "command",
        choices=["play", "pause", "play-pause", "next", "previous", "stop", "status"],
        help="playerctl command to execute"
    )

    # Optional: match playerctl’s filters
    parser.add_argument(
         "--player",
        help="Target a specific player (optional, e.g. spotify, vlc, etc.)"
    )
    parser.add_argument(
           "extra_args",
           nargs=argparse.REMAINDER,
           help="Additional args to forward verbatim"
    ) 

    args = parser.parse_args()

    player = select_player(args)
    
    if not player:
        print("No player found", file=sys.stderr)

    cmd = ["playerctl", "-p", player, args.command] + args.extra_args
    remember_last_player(player)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
