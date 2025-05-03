def init(link_to=None, log_name="Framer", hook_error=False):

    # python module import
    import os
    import sys
    import types
    import functools

    # local module import
    from . import helper

    # create framer
    framer = types.SimpleNamespace()
    framer.helper = helper
    framer.logger = functools.partial(framer.helper.logger, log_name)

    # temporary logger for init
    init_logger = functools.partial(framer.helper.logger, "Init")

    # enable error hook
    sys.excepthook = framer.helper.global_except_hook

    # load env
    if os.path.exists("env.json"):
        init_logger("Loading env.json...")
        import json

        with open("./env.json", "r", encoding="UTF-8") as f:
            env = json.load(f)
        framer.env = types.SimpleNamespace()
        for key, value in env.items():
            init_logger(f"Setting {key} to {value}...")
            setattr(framer.env, key, value)

    # check modules
    init_logger("Checking modules...")

    if framer.helper.no_framerpkg():
        raise FileNotFoundError(
            "No framerpkg.json found, please run `python3 -m Framer init` first."
        )

    if framer.helper.no_framer_modules():
        framer.helper.init_dir("./framer_modules")

    # if disable error hook
    if not hook_error:
        sys.excepthook = sys.__excepthook__

    # return framer
    init_logger("Framer initialized!")
    if link_to is None:
        return framer
    else:
        for attr in dir(framer):
            if not attr.startswith("__"):
                sys.modules[link_to].__dict__[attr] = getattr(framer, attr)
        return
