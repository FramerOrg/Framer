def init(link_to=None, log_name="Framer", hook_error=False):

    # python module import
    import os
    import sys
    import types
    import functools
    import traceback

    # local module import
    from . import helper

    # create framer
    framer = types.SimpleNamespace()
    framer.helper = helper
    framer.logger = functools.partial(framer.helper.logger, log_name)

    # temporary logger for init
    init_logger = functools.partial(framer.helper.logger, "Init")

    # if enable error hook
    if hook_error:
        sys.excepthook = framer.helper.global_except_hook

    try:

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

    except:
        init_logger(traceback.format_exc())

    # return framer
    if link_to is None:
        return framer
    else:
        for attr in dir(framer):
            if not attr.startswith("__"):
                sys.modules[link_to].__dict__[attr] = getattr(framer, attr)
