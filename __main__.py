import argparse
import os
import sys
import time
import subprocess
import functools
import random
import urllib.request
import zipfile

# import helper
from . import helper

# python executable
python = sys.executable

# framer repo
framer_repo = "https://github.com/runoneall/Framer.git"

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
                helper.json_dump(
                    {
                        "modules": (
                            helper.load_installed_modules()
                            if not helper.no_framer_modules()
                            else []
                        ),
                        "disable": [],
                        "origins": [],
                        "module_map": {},
                    }
                ),
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


class FramerUpdateAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger("Update Framer...")
        helper.init_dir("update_tmp")
        fetch_status = self.exec_command("git clone {} update_tmp".format(framer_repo))
        if fetch_status != 0:
            logger("Fetch Framer Failed")
            helper.init_dir("update_tmp", remove=True)
            return
        helper.init_dir("Framer", remove=True)
        os.rename("update_tmp", "Framer")
        logger("Update Framer Done")

    def exec_command(self, command):
        return os.system(command)


class EnvInitAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger("Init Env File...")
        if helper.no_env():
            helper.write_file("env.json", "{}")
        logger("Init Env File Done")


class EnvListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        env = helper.load_env()
        logger(
            "Env Links: \n- {}".format(
                "\n- ".join([f"{key} => {value}" for key, value in env.items()])
            )
        )


class EnvSetAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        key = values[0]
        value = self.parse_env_value(values[1])
        env = helper.load_env()

        # write env file
        logger(f"Set Env {key} => {value}")
        env[key] = value
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


class EnvDelAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        key = values[0]
        env = helper.load_env()

        # write env file
        logger(f"Delete Env {key}")
        if key in env:
            del env[key]
        helper.write_file("env.json", helper.json_dump(env))


class RunnerConfigAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if option_string == "--exit-on-finish":
            runner_config["exit_on_finish"] = True
        if option_string == "--restart-on-error":
            runner_config["restart_on_error"] = True
        if option_string == "--restart-sleep":
            runner_config["restart_sleep"] = int(values[0])
        if option_string == "--restart-on-file-change":
            runner_config["restart_on_file_change"] = True


class RunnerStartAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger("Start Runner...")
        command = [python] + values
        self.file_watchs = []
        if runner_config["restart_on_file_change"] == True:
            logger("Get File Watch List...")
            self.get_watch_list()
            logger("Watch List: \n- {}".format("\n- ".join(self.file_watchs)))

        # run command
        self.process = subprocess.Popen(command)

        # process manage
        try:
            while True:

                # check file change
                if self.check_file_change() == True:
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
            logger("KeyboardInterrupt, Stop Runner...")
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


class OriginAddAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):

        # origin url
        origin = values[0]
        logger(f"Add {origin}")

        # load framerpkg
        if helper.no_framerpkg():
            main_parser.parse_args(["--init"])
        framerpkg = helper.load_framerpkg()

        # add origin
        if origin not in framerpkg["origins"]:
            framerpkg["origins"].append(origin)
            helper.write_file("./framerpkg.json", helper.json_dump(framerpkg))
        logger(f"Add Done")


class OriginDelAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        origin = values[0]
        logger(f"Delete {origin}")

        # load framerpkg
        if helper.no_framerpkg():
            main_parser.parse_args(["--init"])
        framerpkg = helper.load_framerpkg()

        # delete origin
        if origin in framerpkg["origins"]:
            framerpkg["origins"].remove(origin)
            helper.write_file("./framerpkg.json", helper.json_dump(framerpkg))
        logger(f"Delete Done")


class OriginListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        framerpkg = helper.load_framerpkg()
        logger("Origins: \n- {}".format("\n- ".join(framerpkg["origins"])))


class OriginSyncAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        framerpkg = helper.load_framerpkg()

        # fetch origins
        for origin_url in framerpkg["origins"]:
            origin_map = helper.json_load(self.http_text_get(f"{origin_url}/map.json"))
            origin_modules = origin_map["modules"]

            # fetch modules
            for module_name in origin_modules:
                local_module_map = {}

                module_info = helper.json_load(
                    self.http_text_get(f"{origin_url}/{module_name}/info.json")
                )

                # readme.md
                m_desc = module_info["description"]
                if m_desc.startswith("@"):
                    m_readme = m_desc[1:]
                    m_desc = f"{origin_url}/{module_name}/{m_readme}"

                local_module_name = "{}@{}".format(module_name, origin_map["name"])
                local_module_map["author"] = module_info["author"]
                local_module_map["description"] = m_desc
                local_module_map["versions"] = {}

                # latest version
                version_latest = self.http_text_get(
                    f"{origin_url}/{module_name}/latest.txt"
                )
                local_module_map["latest"] = version_latest

                # fetch versions
                for version in module_info["versions"]:
                    file_zip_url = f"{origin_url}/{module_name}/{version}/file.zip"
                    version_require = helper.json_load(
                        self.http_text_get(
                            f"{origin_url}/{module_name}/{version}/require.json"
                        )
                    )
                    local_module_map["versions"][version] = {
                        "download": file_zip_url,
                        "require": version_require,
                    }

                # save module map
                framerpkg["module_map"][local_module_name] = local_module_map

        # save sync result
        helper.write_file("./framerpkg.json", helper.json_dump(framerpkg))
        logger("Sync Done")

    def http_text_get(self, url, retry=3):
        logger(f"Fetch {url}")
        while retry > 0:
            try:
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "Framer-CLI/1.0 (Official)",
                            "Cache-Control": "no-cache",
                            "Pragma": "no-cache",
                        },
                    )
                )
                return response.read().decode("utf-8")
            except KeyboardInterrupt:
                logger("KeyboardInterrupt, Stop Fetch...")
                return None
            except Exception:
                logger(f"Fetch {url} Failed, Retry {retry}...")
                retry -= 1
        logger(f"Fetch {url} Failed")
        return None


class OriginMakeAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):

        # init maker dir
        base_dir = "./maker_release"
        sys.path.append("./framer_modules")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # load target modules
        modules = helper.load_installed_modules()
        logger("Target To Make: \n- {}".format("\n- ".join(modules)))

        # load maker config
        if not os.path.exists("./origin-maker.json"):
            maker_config = {
                "name": input("Enter Name: "),
                "base": input("Enter Base URL: "),
            }
            helper.write_file("./origin-maker.json", helper.json_dump(maker_config))
        maker_config = helper.json_load(helper.read_file("./origin-maker.json"))
        logger(
            "Maker Config: \n- {}".format(
                "\n- ".join([f"{key}: {value}" for key, value in maker_config.items()])
            )
        )

        # make origin map
        origin_map = helper.json_dump({**maker_config, "modules": modules})
        helper.write_file(f"{base_dir}/map.json", origin_map)
        logger(f"Make Origin Map: \n{origin_map}")

        # process modules
        for module_name in modules:
            logger(f"Process Module {module_name}")

            # get module info
            moduleInfo = __import__(module_name).moduleInfo
            logger(
                "Module {} Info: \n{}".format(module_name, helper.json_dump(moduleInfo))
            )

            # make module dir
            module_base = f"{base_dir}/{module_name}"
            if not os.path.exists(module_base):
                os.makedirs(module_base)

            # latest version file
            version_latest = moduleInfo["version"]
            helper.write_file(f"{module_base}/latest.txt", version_latest)
            logger(f"Module {module_name} Latest: {version_latest}")

            # process module info
            del moduleInfo["version"]
            if os.path.exists(f"{module_base}/info.json"):
                module_info = helper.json_load(
                    helper.read_file(f"{module_base}/info.json")
                )
                if version_latest in module_info["versions"]:
                    logger(f"Module {module_name} Version {version_latest} Exists")
                    continue
            else:
                module_info = {**moduleInfo, "versions": []}
            module_info["versions"].append(version_latest)

            # write module info
            json_module_info = helper.json_dump(module_info)
            helper.write_file(f"{module_base}/info.json", json_module_info)
            logger("Module {} Map: \n{}".format(module_name, json_module_info))

            # process versions
            logger(f"Process Module {module_name} Version {version_latest}")

            # make version dir
            version_base = f"{module_base}/{version_latest}"
            if not os.path.exists(version_base):
                os.makedirs(version_base)

            # copy version require
            version_require = helper.read_file(
                f"./framer_modules/{module_name}/require.json"
            )
            helper.write_file(
                f"{version_base}/require.json",
                version_require,
            )
            logger(
                "Copy Module {} Version {} Require: \n{}".format(
                    module_name, version_latest, version_require
                )
            )

            # zip module
            zip_from = f"./framer_modules/{module_name}"
            zip_to = f"{version_base}/file.zip"
            self.create_zip(
                source_dir=zip_from,
                zip_path=zip_to,
                exclude_dirs=["__pycache__"],
                exclude_files_startswith=["."],
                exclude_hidden=True,
            )

    def create_zip(
        self,
        source_dir,
        zip_path,
        exclude_dirs=None,
        exclude_files_startswith=None,
        exclude_hidden=True,
        compression=zipfile.ZIP_DEFLATED,
    ):
        # init exclude
        exclude_dirs = exclude_dirs or []
        exclude_files_startswith = exclude_files_startswith or []

        # check target dir
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)

        with zipfile.ZipFile(zip_path, "w", compression) as zf:
            for root, dirs, files in os.walk(source_dir):
                # process exclude dirs
                dirs[:] = [
                    d
                    for d in dirs
                    if not (
                        (exclude_hidden and d.startswith("."))  # exclude hidden dir
                        or (d in exclude_dirs)  # user specified exclude dir
                    )
                ]

                # process exclude files
                for file in files:
                    if (exclude_hidden and file.startswith(".")) or any(
                        file.startswith(p) for p in exclude_files_startswith
                    ):
                        continue

                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zf.write(file_path, arcname)


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
main_parser.add_argument(
    "--update", help="Update Framer", action=FramerUpdateAction, nargs=0
)
env_parser = LoggerParser(prog="env", description="Framer CLI", add_help=False)
env_parser.add_argument(
    "-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0
)
env_parser.add_argument("--init", help="Init Env File", action=EnvInitAction, nargs=0)
env_parser.add_argument(
    "-l", "--list", help="List Environments", action=EnvListAction, nargs=0
)
env_parser.add_argument(
    "--set",
    help="Set Environment, TYPE can be 'str', 'int', 'float', 'bool', Default 'str'",
    action=EnvSetAction,
    nargs=2,
    metavar=("KEY", "[TYPE:]VALUE"),
)
env_parser.add_argument(
    "--del",
    help="Delete Environment",
    action=EnvDelAction,
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
    action=RunnerConfigAction,
    nargs=0,
)
runner_parser.add_argument(
    "--restart-on-error",
    help="Restart on Error",
    action=RunnerConfigAction,
    nargs=0,
)
runner_parser.add_argument(
    "--restart-sleep",
    help="Restart Sleep Seconds",
    action=RunnerConfigAction,
    nargs=1,
    metavar="SECONDS",
)
runner_parser.add_argument(
    "--restart-on-file-change",
    help="Restart on File Change",
    action=RunnerConfigAction,
    nargs=0,
)
runner_parser.add_argument(
    "--start",
    help="Start Runner",
    action=RunnerStartAction,
    nargs=argparse.REMAINDER,
)
origin_parser = LoggerParser(prog="origin", description="Framer CLI", add_help=False)
origin_parser.add_argument(
    "-h", "--help", help="Show Help", action=ShowHelpAction, nargs=0
)
origin_parser.add_argument(
    "--add", help="Add Origin", action=OriginAddAction, nargs=1, metavar="ORIGIN"
)
origin_parser.add_argument(
    "-l", "--list", help="List Origins", action=OriginListAction, nargs=0
)
origin_parser.add_argument(
    "--del", help="Delete Origin", action=OriginDelAction, nargs=1, metavar="ORIGIN"
)
origin_parser.add_argument(
    "--sync", help="Sync Origin", action=OriginSyncAction, nargs=0
)
origin_parser.add_argument(
    "--make", help="Make Origin", action=OriginMakeAction, nargs=0
)
main_subparsers = main_parser.add_subparsers(dest="subparsers")
main_subparsers.add_parser("env", parents=[env_parser], add_help=False)
main_subparsers.add_parser("runner", parents=[runner_parser], add_help=False)
main_subparsers.add_parser("origin", parents=[origin_parser], add_help=False)


# show help if no arguments
if len(sys.argv) == 1:
    main_parser.parse_args(["--help"])

# parse arguments
else:
    main_parser.parse_args()
