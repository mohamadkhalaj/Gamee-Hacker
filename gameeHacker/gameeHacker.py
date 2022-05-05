import argparse
import os
import re
import sys
from random import randint

from core import GameeHacker

__help__ = f"""Usage:
{__file__} [--argument] [value]

Args                 Description                       Default
-h, --help           Throwback this help manaul        False
-u, --url            Url of your game in gamee         None
-t, --time           Play time                         Random
-s, --score   	     Your score                        None

	--get-rank       Rank of you in current game   False
	--get-record     Your record in current game   False
	--get-summery    All of your data in gamee     False
    --get-name       Name of game                  False 

"""


class Cli:

    WHITE = "\033[0m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    LINEUP = "\033[F"

    MIXTURE = {
        "WHITE": "\033[0m",
        "PURPLE": "\033[95m",
        "CYAN": "\033[96m",
        "DARKCYAN": "\033[36m",
        "BLUE": "\033[94m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "END": "\033[0m",
        "LINEUP": "\033[F",
    }

    VACANT = {
        "WHITE": "",
        "PURPLE": "",
        "CYAN": "",
        "DARKCYAN": "",
        "BLUE": "",
        "GREEN": "",
        "YELLOW": "",
        "RED": "",
        "BOLD": "",
        "UNDERLINE": "",
        "END": "",
        "LINEUP": "",
    }

    def __init__(self, opts):

        if not self.support_colors:
            self.win_colors()

        self.help(opts.help)

        self.required_fields = (
            True
            if self.required_field(opts)
            else self.halt("-u/--url URL, -s/--score SCORE are required.", True, self.RED)
        )

        self.url = (
            opts.url if self.is_valid_url(opts.url) else self.halt("Invalid URL.", True, self.RED)
        )

        self.score = (
            opts.score if opts.score > 0 else self.halt("Score must be >= 1", True, self.RED)
        )

        self.time = opts.time if opts.time > 0 else self.halt("Time must be >= 1", True, self.RED)

        self.record = opts.record
        self.rank = opts.rank
        self.summery = opts.summery
        self.name = opts.name

        self.game_obj = GameeHacker(self.url, self.score, self.time)
        self.start_hacking()

    def support_colors(self):
        plat = sys.platform
        supported_platform = plat != "Pocket PC" and (plat != "win32" or "ANSICON" in os.environ)
        is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        if not supported_platform or not is_a_tty:
            return False
        return True

    def required_field(self, opts):
        if opts.url == None or opts.score == None:
            return False
        return True

    def win_colors(self):
        self.WHITE = ""
        self.PURPLE = ""
        self.CYAN = ""
        self.DARKCYAN = ""
        self.BLUE = ""
        self.GREEN = ""
        self.YELLOW = ""
        self.RED = ""
        self.BOLD = ""
        self.UNDERLINE = ""
        self.END = ""
        self.MIXTURE = {
            "WHITE": "",
            "PURPLE": "",
            "CYAN": "",
            "DARKCYAN": "",
            "BLUE": "",
            "GREEN": "",
            "YELLOW": "",
            "RED": "",
            "BOLD": "",
            "UNDERLINE": "",
            "END": "",
            "LINEUP": "",
        }

        for key in list(self.MIXTURE.items()):
            self.MIXTURE[key] = ""

    def help(self, _help):
        if _help:
            sys.exit(__help__)

    def halt(self, statement, exit, *colors):
        cc = ""
        cc = "".join([color for color in colors])
        print("{mix}[~]{end} {statement}".format(mix=cc, end=self.END, statement=statement))
        if exit:
            sys.exit(-1)

    def print(self, sig, statement, *colors):
        cc = ""
        cc = "".join([color for color in colors])
        print(
            "{mix}[{sig}]{end} {statement}".format(
                sig=sig, mix=cc, end=self.END, statement=statement
            ),
            end="\n\n",
        )

    def is_valid_url(self, url):

        regex = (
            "((http|https)://)(www.)?"
            + "[a-zA-Z0-9@:%._\\+~#?&//=]"
            + "{2,256}\\.[a-z]"
            + "{2,6}\\b([-a-zA-Z0-9@:%"
            + "._\\+~#?&//=]*)"
        )

        p = re.compile(regex)

        if url == None or "prizes.gamee.com/game-bot/" not in url:
            return False
        if re.search(p, url):
            return True
        else:
            return False

    def start_hacking(self):
        self.game_obj.send_score()
        if self.name:
            self.print("!", "Game name:\n" + str(self.game_obj.get_game_name()), self.PURPLE)
        if self.summery:
            self.print("!", "User summery:", self.RED)
            self.game_obj.get_user_summery_pprint()
        if self.rank:
            self.print("!", "User rank:\n" + str(self.game_obj.get_user_rank()), self.GREEN)
        if self.record:
            self.print("!", "User record:\n" + str(self.game_obj.get_user_record()), self.BLUE)


def main():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("-h", "--help", dest="help", default=False, action="store_true")
    parser.add_argument("-u", "--url", dest="url", default="", type=str)
    parser.add_argument("-s", "--score", dest="score", type=int)
    parser.add_argument("-t", "--time", dest="time", default=randint(10, 2000), type=int)
    parser.add_argument("--get-rank", dest="rank", default=False, action="store_true")
    parser.add_argument("--get-record", dest="record", default=False, action="store_true")
    parser.add_argument("--get-summery", dest="summery", default=False, action="store_true")
    parser.add_argument("--get-name", dest="name", default=False, action="store_true")

    options = parser.parse_args()
    parser = Cli(options)


if __name__ == "__main__":
    main()
