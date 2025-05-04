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

    # temporary logger for init
    init_logger = functools.partial(framer.helper.logger, "Init")

    # enable error hook
    sys.excepthook = framer.helper.global_except_hook

    # load env
    if os.path.exists("env.json"):
        init_logger("Loading env.json...")

        env = framer.helper.load_env()
        framer.env = types.SimpleNamespace()
        for key, value in env.items():
            setattr(framer.env, key, value)

        init_logger(
            "Env Links: \n- {}".format(
                "\n- ".join([f"{key} => {value}" for key, value in env.items()])
            )
        )

    # check modules
    init_logger("Checking modules...")

    if framer.helper.no_framerpkg():
        raise FileNotFoundError(
            "No framerpkg.json found, please run `python3 -m Framer init` first."
        )

    if framer.helper.no_framer_modules():
        framer.helper.init_dir("./framer_modules")
    sys.path.append("./framer_modules")

    # check module folders
    installed_modules = [
        m
        for m in os.listdir("./framer_modules")
        if os.path.isdir(f"./framer_modules/{m}") and not m.startswith(".")
    ]
    init_logger("Installed Modules: \n- {}".format("\n- ".join(installed_modules)))

    # check package config
    framerpkg = framer.helper.load_framerpkg()

    all_modules = list(framerpkg["modules"].keys())
    init_logger("All Modules: \n- {}".format("\n- ".join(all_modules)))

    disabled_modules = framerpkg["disable"]
    init_logger("Disabled Modules: \n- {}".format("\n- ".join(disabled_modules)))

    # map installed modules info
    init_logger("Mapping installed modules info...")
    installed_modules_info = {}
    for m in installed_modules:
        moduleInfo = __import__(m).moduleInfo
        installed_modules_info[m] = moduleInfo
    init_logger(
        "Installed Modules Info: \n\n- {}".format(
            "\n\n- ".join(
                [
                    "{}: \n  @{}".format(
                        m, "\n  @".join([f"{k}: {v}" for k, v in info.items()])
                    )
                    for m, info in installed_modules_info.items()
                ]
            )
        )
    )

    # import installed modules
    for m in installed_modules:
        if m in disabled_modules:
            continue

        # check dependencies
        require = framer.helper.load_require(m)
        dep = require["dependencies"]

        for d_name, d_version in dep.items():

            # if dependency not installed
            if d_name not in installed_modules:
                raise ImportError(
                    "Module {} require {} version {}, but {} not installed.".format(
                        m, d_name, d_version, d_name
                    )
                )

            # if dependency version not match
            if d_version != installed_modules_info[d_name]["version"]:
                raise ImportError(
                    "Module {} require {} version {}, but {} version {} installed.".format(
                        m,
                        d_name,
                        d_version,
                        d_name,
                        installed_modules_info[d_name]["version"],
                    )
                )

            # check if dependency disabled
            if d_name in disabled_modules:
                raise ImportError(
                    "Module {} require {} version {}, but {} disabled.".format(
                        m, d_name, d_version, d_name
                    )
                )

        # import module
        init_logger(f"Importing module {m}...")
        m_obj = __import__(m)

        # import module main
        if not hasattr(m_obj, "moduleMain"):
            raise ImportError(f"Module {m} has no Entry Point: moduleMain")
        module = m_obj.moduleMain(framer, functools.partial(framer.helper.logger, m))

        # add module to framer
        setattr(module, "moduleInfo", installed_modules_info[m])
        setattr(framer, m, module)

    # if disable error hook
    if not hook_error:
        sys.excepthook = sys.__excepthook__

    # create main logger
    framer.logger = functools.partial(framer.helper.logger, log_name)

    # return framer
    init_logger("Framer Init Complete!")
    if link_to is None:
        return framer
    else:
        for attr in dir(framer):
            if not attr.startswith("__"):
                sys.modules[link_to].__dict__[attr] = getattr(framer, attr)
        return framer
