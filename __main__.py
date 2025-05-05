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
Framer.init(link_to=__name__, log_name="Test", hook_error=True)
logger("Hello Framer!")"""
            )
        self.test_file = test_file
        logger(f"Create {test_file}")


# add arguments
parser.add_argument("-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0)
parser.add_argument("--test", help="Test Framer", action=TestFramerAction, nargs=0)

# show help if no arguments
if len(sys.argv) == 1:
    parser.parse_args(["--help"])

# parse arguments
else:
    args = parser.parse_args()
