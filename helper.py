import os
import json


def logger(from_module: str, message: str, max_width: int = None):
    import time

    def format_with_wrap(msg: str, width: int):
        import textwrap

        result = []
        for line in msg.splitlines(keepends=True):
            if len(line.strip()) == 0 or len(line) <= width:
                result.append(line)
            else:
                wrapped_lines = textwrap.wrap(
                    line, width=width, break_long_words=True, replace_whitespace=False
                )
                result.extend([l + "\n" for l in wrapped_lines])
        return "".join(result)

    def get_terminal_width():
        try:
            columns = os.get_terminal_size().columns - 2
            return columns
        except (AttributeError, OSError):
            return 80

    if max_width is None:
        max_width = get_terminal_width()

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    message = format_with_wrap(str(message), width=max_width)

    # if message only one line
    if "\n" not in message:
        print(f"* {from_module} ({current_time}) {message}")
        return

    # if message multiple lines
    if "\n" in message:
        print(f"* {from_module} ({current_time})")
        print("|", "\n| ".join(message.split("\n")), "\n")
        return


def global_except_hook(exc_type, exc_value, exc_traceback):
    import traceback

    logger(
        "ErrHooker",
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
    )


def init_dir(path: str):
    import shutil

    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def no_framerpkg() -> bool:
    if not os.path.exists("./framerpkg.json") or not os.path.isfile("./framerpkg.json"):
        return True
    return False


def no_framer_modules() -> bool:
    if not os.path.exists("./framer_modules") or not os.path.isdir("./framer_modules"):
        return True
    return False


def no_env() -> bool:
    if not os.path.exists("./env.json") or not os.path.isfile("./env.json"):
        return True
    return False


def load_env():
    with open("./env.json", "r", encoding="UTF-8") as f:
        return json.load(f)


def load_framerpkg():
    with open("./framerpkg.json", "r", encoding="UTF-8") as f:
        return json.load(f)


def load_require(module_name: str):
    with open(
        f"./framer_modules/{module_name}/require.json", "r", encoding="UTF-8"
    ) as f:
        return json.load(f)


def write_file(path: str, content: str):
    with open(path, "w", encoding="UTF-8") as f:
        f.write(content)


def json_dump(data):
    return json.dumps(data, indent=4, ensure_ascii=False)
