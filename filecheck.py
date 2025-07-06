import os

_IS_EXISTS: dict[str, bool] = {}


def no_framerpkg() -> bool:
    path = os.path.join(os.getcwd(), "framerpkg.json")

    if path not in _IS_EXISTS:
        _IS_EXISTS[path] = os.path.exists(path) and os.path.isfile(path)
    return not _IS_EXISTS[path]


def no_framer_modules() -> bool:
    path = os.path.join(os.getcwd(), "framer_modules")

    if path not in _IS_EXISTS:
        _IS_EXISTS[path] = os.path.exists(path) and os.path.isdir(path)
    return not _IS_EXISTS[path]


def no_env() -> bool:
    path = os.path.join(os.getcwd(), "env.json")

    if path not in _IS_EXISTS:
        _IS_EXISTS[path] = os.path.exists(path) and os.path.isfile(path)
    return not _IS_EXISTS[path]
