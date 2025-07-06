import os
import json
import typing

_ENV_FILE_PATH = os.path.join(os.getcwd(), "env.json")


def load_env() -> dict[str, typing.Any]:
    with open(_ENV_FILE_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)
