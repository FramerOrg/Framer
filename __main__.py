import argparse
import os
import sys
import shutil
import functools
import random

# import helper
from . import helper

# python executable
python = sys.executable


# CLI init
logger = functools.partial(helper.logger, "CLI")
sys.excepthook = helper.global_except_hook


# parser init
class LoggerParser(argparse.ArgumentParser):
    def error(self, message):
        logger(message)
        sys.exit(1)


parser = LoggerParser(description="Framer CLI", add_help=False)


class ShowHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger(parser.format_help())


class TestFramerAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger("Testing Framer...")
        self.generate_test_file()

        try:
            os.system(f"{python} {self.test_file}")
        finally:
            if os.path.exists(self.test_file):
                os.remove(self.test_file)

    def generate_test_file(self):
        test_file = (
            "test_framer_"
            + "".join(
                random.sample(
                    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 10
                )
            )
            + ".py"
        )
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(
                """import Framer
Framer.init(link_to=__name__, log_name="CLI", hook_error=True)
logger("Hello Framer!")"""
            )
        self.test_file = test_file
        logger(f"Create {test_file}")


class InitProjectAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger("Init Project...")
        if helper.no_framerpkg():
            with open("./framerpkg.json", "w", encoding="UTF-8") as f:
                f.write(
                    """{
    "modules": {},
    "disable": []
}"""
                )
        if helper.no_framer_modules():
            helper.init_dir("./framer_modules")
        logger("Init Project Done")


class EnvAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(namespace, option_string, values)


# add arguments
parser.add_argument("-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0)
parser.add_argument(
    "-t", "--test", help="Test Framer", action=TestFramerAction, nargs=0
)
parser.add_argument("--init", help="Init Project", action=InitProjectAction, nargs=0)
env_parser = parser.add_subparsers(dest="env", help="Environment").add_parser(
    "env", help="Environment Manager", add_help=False
)
env_parser.add_argument(
    "-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0
)

# show help if no arguments
if len(sys.argv) == 1:
    parser.parse_args(["--help"])

# parse arguments
else:
    parser.parse_args()
