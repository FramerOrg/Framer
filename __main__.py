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
        helper.write_file(
            test_file,
            """import Framer
Framer.init(link_to=__name__, log_name="CLI", hook_error=True)
logger("Hello Framer!")""",
        )
        self.test_file = test_file
        logger(f"Create {test_file}")


class InitProjectAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger("Init Project...")
        if helper.no_framerpkg():
            helper.write_file(
                "./framerpkg.json",
                """{
    "modules": {},
    "disable": []
}""",
            )
        if helper.no_framer_modules():
            helper.init_dir("./framer_modules")
        logger("Init Project Done")


class ModuleCLIAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(option_string, values)


class EnvAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):

        # init env file
        if option_string == "--init":
            logger("Init Env File...")
            if helper.no_env():
                helper.write_file("env.json", "{}")
            logger("Init Env File Done")

        # list envs
        if option_string == "-l" or option_string == "--list":
            env = helper.load_env()
            logger(
                "Env Links: \n- {}".format(
                    "\n- ".join([f"{key} => {value}" for key, value in env.items()])
                )
            )

        # set env
        if option_string == "--set":
            key = values[0]
            value = self.parse_env_value(values[1])
            env = helper.load_env()

            # write env file
            logger(f"Set Env {key} => {value}")
            env[key] = value
            helper.write_file("env.json", helper.json_dump(env))

        # delete env
        if option_string == "--del":
            key = values[0]
            env = helper.load_env()

            # write env file
            logger(f"Delete Env {key}")
            if key in env:
                del env[key]
            helper.write_file("env.json", helper.json_dump(env))

    def parse_env_value(self, value):
        if ":" not in value:
            return value
        else:
            value_type, value = value.split(":", 1)
            if value_type == "str":
                return value
            elif value_type == "int":
                return int(value)
            elif value_type == "float":
                return float(value)
            elif value_type == "bool":
                return value.lower() == "true"
            else:
                logger(f"Invalid value type: {value_type}")
                return value


# add arguments
parser.add_argument("-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0)
parser.add_argument(
    "-v", "--version", help="Show Version", action="version", version="1.0 (Official)"
)
parser.add_argument(
    "-t", "--test", help="Test Framer", action=TestFramerAction, nargs=0
)
parser.add_argument("--init", help="Init Project", action=InitProjectAction, nargs=0)
parser.add_argument(
    "-m",
    "--module",
    help="Load Module CLI",
    action=ModuleCLIAction,
    nargs=argparse.REMAINDER,
)
env_parser = parser.add_subparsers(dest="env", help="Env Args").add_parser(
    "env", help="Environment Manager", add_help=False
)
env_parser.add_argument(
    "-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0
)
env_parser.add_argument("--init", help="Init Env File", action=EnvAction, nargs=0)
env_parser.add_argument(
    "-l", "--list", help="List Environments", action=EnvAction, nargs=0
)
env_parser.add_argument(
    "--set",
    help="Set Environment, TYPE can be 'str', 'int', 'float', 'bool', Default 'str'",
    action=EnvAction,
    nargs=2,
    metavar=("KEY", "[TYPE:]VALUE"),
)
env_parser.add_argument(
    "--del",
    help="Delete Environment",
    action=EnvAction,
    nargs=1,
    metavar="KEY",
)

# show help if no arguments
if len(sys.argv) == 1:
    parser.parse_args(["--help"])

# parse arguments
else:
    parser.parse_args()
