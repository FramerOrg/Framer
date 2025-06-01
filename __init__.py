def init(
    link_to=None,
    log_name="Framer",
    hook_error=False,
    redirect_output=False,
):

    # python module import
    import sys
    import types
    import functools

    # local module import
    from . import helper

    # create framer
    framer = types.SimpleNamespace()
    framer.helper = helper
    framer.link_to = link_to

    # temporary logger for init
    init_logger = functools.partial(framer.helper.logger, "Init")

    # enable error hook
    sys.excepthook = framer.helper.global_except_hook

    # redirect output
    if redirect_output != False:
        init_logger("Stdout Link To: {}".format(redirect_output.__name__))
        sys.stdout = framer.helper.CustomStdout(redirect_output)

    # load env
    if not framer.helper.no_env():
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

    # check framerpkg and framer_modules
    init_logger("Checking modules...")

    if framer.helper.no_framerpkg():
        raise FileNotFoundError(
            "No framerpkg.json found, please run `python3 -m Framer --init` first."
        )

    if framer.helper.no_framer_modules():
        framer.helper.init_dir("./framer_modules")
    sys.path.append("./framer_modules")

    # check package config
    framerpkg = framer.helper.load_framerpkg()

    installed_modules = framerpkg["modules"]
    init_logger("Installed Modules: \n- {}".format("\n- ".join(installed_modules)))

    disabled_modules = framerpkg["disable"]
    init_logger("Disabled Modules: \n- {}".format("\n- ".join(disabled_modules)))

    # map installed modules info
    init_logger("Mapping installed modules info...")
    installed_modules_info = {}
    sorted_installed_modules = []
    for m in installed_modules:
        moduleInfo = __import__(m).moduleInfo
        installed_modules_info[m] = moduleInfo

        # if is hooker
        if "hooker" in moduleInfo and moduleInfo["hooker"] == True:
            sorted_installed_modules.insert(0, m)
        else:
            sorted_installed_modules.append(m)
    installed_modules = sorted_installed_modules

    # print installed modules info
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

        # load require
        require = framer.helper.load_require(m)

        # check dependencies
        for dep in require["dependencies"]:

            # if dependency not installed
            if dep not in installed_modules:
                raise ImportError(f"Module {m} require {dep}, but {dep} not installed.")

            # check if dependency disabled
            if dep in disabled_modules:
                raise ImportError(f"Module {m} require {dep}, but {dep} disabled.")

        # check pip dependencies
        for pip_dep in require["pip_dependencies"]:
            if helper.no_pip_module(pip_dep):
                raise ImportError(
                    f"Module {m} require {pip_dep}, but {pip_dep} not installed."
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
    if framer.link_to is None:
        return framer
    else:
        for attr in dir(framer):
            if not attr.startswith("__"):
                sys.modules[framer.link_to].__dict__[attr] = getattr(framer, attr)
        return framer
