import json
import os
import typing


def load_framerpkg() -> dict[str, typing.Any]:
    path = os.path.join(os.getcwd(), "framerpkg.json")

    with open(path, "r", encoding="UTF-8") as f:
        return json.load(f)


def load_require(module_name: str) -> dict[str, typing.Any]:
    path = os.path.join(os.getcwd(), "framer_modules", module_name, "require.json")

    with open(path, "r", encoding="UTF-8") as f:
        return json.load(f)
