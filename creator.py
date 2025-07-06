import os
import json


def create_framerpkg() -> None:
    path = os.path.join(os.getcwd(), "framerpkg.json")

    with open(path, "w") as f:
        json.dump(
            {
                "modules": [],
                "disable": [],
                "origins": [],
            },
            f,
        )


def create_framer_modules() -> None:
    path = os.path.join(os.getcwd(), "framer_modules")
    os.mkdir(path)
