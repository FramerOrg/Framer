import argparse
import os
import sys
import time
import subprocess
import functools
import random

# import helper
from . import helper

# python executable
python = sys.executable

# CLI init
logger = functools.partial(helper.logger, "CLI")
sys.excepthook = helper.global_except_hook

# init runner
runner_config = {
    "exit_on_finish": False,
    "restart_on_error": False,
    "restart_sleep": 1,
    "restart_on_file_change": False,
}


# parser class
class LoggerParser(argparse.ArgumentParser):
    def error(self, message):
        logger(message)
        sys.exit(1)


# actions
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
        module = values[0]
        args = values[1:]
        installed_modules = helper.load_installed_modules()

        # if module not installed
        if module not in installed_modules:
            raise ImportError(f"Module {module} not installed")

        # import module
        sys.path.append("./framer_modules")
        module_obj = __import__(module)

        # if no entry point
        if not hasattr(module_obj, "cliMain"):
            raise ImportError(f"Module {module} has no Entry Point: cliMain")

        # run entry point
        module_obj.cliMain(args)


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


class RunnerAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):

        # config
        if option_string == "--exit-on-finish":
            runner_config["exit_on_finish"] = True
        if option_string == "--restart-on-error":
            runner_config["restart_on_error"] = True
        if option_string == "--restart-sleep":
            runner_config["restart_sleep"] = int(values[0])
        if option_string == "--restart-on-file-change":
            runner_config["restart_on_file_change"] = True

        # start
        if option_string == "--start":
            logger("Start Runner...")
            command = [python] + values
            self.file_watchs = []
            if runner_config["restart_on_file_change"] == True:
                logger("Get File Watch List...")
                self.get_watch_list()
                logger("Watch List: \n- {}".format("\n- ".join(self.file_watchs)))

            # run command
            self.process = subprocess.Popen(command)

            # process manager
            try:
                while True:

                    # check file change
                    if self.check_file_change():
                        if runner_config["restart_on_file_change"] == True:
                            self.stop_runner()
                            self.sleep()
                            self.process = subprocess.Popen(command)

                    if self.process.poll() != None:

                        # script run finish
                        if self.process.returncode == 0:
                            if runner_config["exit_on_finish"] == True:
                                break
                            else:
                                logger(
                                    "Runner Exit {}, Wait Next Event...".format(
                                        self.process.returncode
                                    )
                                )
                                self.sleep()

                        # script run error
                        if self.process.returncode != 0:
                            if runner_config["restart_on_error"] == True:
                                logger(
                                    "Runner Exit {}, Restart".format(
                                        self.process.returncode
                                    )
                                )
                                self.sleep()
                                self.process = subprocess.Popen(command)
                            else:
                                break

            # runner exit
            except KeyboardInterrupt:
                self.stop_runner()
            finally:
                logger("Runner Exit {}".format(self.process.returncode))

    def get_watch_list(self):
        self.file_watchs += [
            f"./{fname}"
            for fname in os.listdir(".")
            if not fname.startswith(".")
            and fname.endswith(".py")
            and os.path.isfile(f"./{fname}")
        ]
        for fbase, _, fnames in os.walk("./framer_modules"):
            self.file_watchs += [
                f"{fbase}/{fname}"
                for fname in fnames
                if not fname.startswith(".")
                and fname.endswith(".py")
                and os.path.isfile(f"{fbase}/{fname}")
            ]
        self.modified_time = {}
        for fname in self.file_watchs:
            self.modified_time[fname] = os.path.getmtime(fname)

    def check_file_change(self):
        for fname in self.file_watchs:
            if os.path.getmtime(fname) != self.modified_time[fname]:
                self.modified_time[fname] = os.path.getmtime(fname)
                logger(f"File {fname} Changed, Restart")
                return True
        return False

    def sleep(self):
        time.sleep(runner_config["restart_sleep"])

    def stop_runner(self):
        try:
            self.process.terminate()
            self.process.wait(timeout=120)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


# parsers
main_parser = LoggerParser(description="Framer CLI", add_help=False)
main_parser.add_argument(
    "-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0
)
main_parser.add_argument(
    "-v", "--version", help="Show Version", action="version", version="1.0 (Official)"
)
main_parser.add_argument(
    "-t", "--test", help="Test Framer", action=TestFramerAction, nargs=0
)
main_parser.add_argument(
    "--init", help="Init Project", action=InitProjectAction, nargs=0
)
main_parser.add_argument(
    "-m",
    "--module",
    help="Load Module CLI",
    action=ModuleCLIAction,
    nargs=argparse.REMAINDER,
)
env_parser = LoggerParser(prog="env", description="Framer CLI", add_help=False)
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
runner_parser = LoggerParser(prog="runner", description="Framer CLI", add_help=False)
runner_parser.add_argument(
    "-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0
)
runner_parser.add_argument(
    "--exit-on-finish",
    help="Exit on Finish",
    action=RunnerAction,
    nargs=0,
)
runner_parser.add_argument(
    "--restart-on-error",
    help="Restart on Error",
    action=RunnerAction,
    nargs=0,
)
runner_parser.add_argument(
    "--restart-sleep",
    help="Restart Sleep Seconds",
    action=RunnerAction,
    nargs=1,
    metavar="SECONDS",
)
runner_parser.add_argument(
    "--restart-on-file-change",
    help="Restart on File Change",
    action=RunnerAction,
    nargs=0,
)
runner_parser.add_argument(
    "--start",
    help="Start Runner",
    action=RunnerAction,
    nargs=argparse.REMAINDER,
)
main_subparsers = main_parser.add_subparsers(dest="subparsers")
main_subparsers.add_parser("env", parents=[env_parser], add_help=False)
main_subparsers.add_parser("runner", parents=[runner_parser], add_help=False)


# show help if no arguments
if len(sys.argv) == 1:
    main_parser.parse_args(["--help"])

# parse arguments
else:
    main_parser.parse_args()
