import os
import sys
import typing

from . import logger, errhook, stdhook, filecheck, env, creator, fileloader, pointer


def init(
    log_name: str = "Framer",
    hook_error: bool = False,
    redirect_output: typing.Union[typing.Callable[[str], None], bool] = False,
) -> pointer.Pointer:

    # create framer
    framer = pointer.Pointer()

    # create helper
    framer.helper = pointer.Pointer(
        # logger
        logger=logger.logger,
        # errhook
        global_except_hook=errhook.global_except_hook,
        # stdhook
        CustomStdout=stdhook.CustomStdout,
        # filecheck
        no_framerpkg=filecheck.no_framerpkg,
        no_framer_modules=filecheck.no_framer_modules,
        no_env=filecheck.no_env,
        # env
        load_env=env.load_env,
        # creator
        create_framerpkg=creator.create_framerpkg,
        create_framer_modules=creator.create_framer_modules,
        # fileloader
        load_framerpkg=fileloader.load_framerpkg,
        load_require=fileloader.load_require,
    )

    # temporary logger for init
    init_logger = lambda msg: framer.helper.logger("Init", msg)

    # enable error hook
    sys.excepthook = framer.helper.global_except_hook

    # redirect output
    if redirect_output is not False:
        sys.stdout = framer.helper.CustomStdout(redirect_output)

    # load env
    if not framer.helper.no_env():
        init_logger("Loading env.json...")
        framer.env = pointer.Pointer(**framer.helper.load_env())

    # check framerpkg
    if framer.helper.no_framerpkg():
        init_logger("Creating framerpkg.json...")
        framer.helper.create_framerpkg()

    # check framer_modules
    if framer.helper.no_framer_modules():
        init_logger("Creating framer_modules directory...")
        framer.helper.create_framer_modules()

    # add framer_modules to sys.path
    sys.path.append(os.path.join(os.getcwd(), "framer_modules"))

    # load framerpkg
    framerpkg = framer.helper.load_framerpkg()
    all_modules = framerpkg["modules"]
    disabled_modules = framerpkg["disable"]

    # create main logger
    framer.logger = lambda msg: framer.helper.logger(log_name, msg)

    # lazy modules loader
    def lazy_load_module(name: str) -> typing.Any:

        # if not in all_modules
        if name not in all_modules:
            raise ImportError(f"Module {name} not found in framerpkg.json")

        # if already loaded
        if hasattr(framer, name):
            return getattr(framer, name)

        # if disabled
        if name in disabled_modules:
            raise ImportError(f"Module {name} is disabled in framerpkg.json")

        # load module require
        require = framer.helper.load_require(name)

        # check dependencies
        for dep in require["dependencies"]:

            # if dependency not installed
            if dep not in all_modules:
                raise ImportError(
                    f"Module {name} requires {dep} which is not installed"
                )

            # check if dependency disabled
            if dep in disabled_modules:
                raise ImportError(f"Module {name} requires {dep} which is disabled")

        # import module
        init_logger(f"Importing module {name}...")
        module = __import__(name)

        # import module main
        if not hasattr(module, "moduleMain"):
            raise ImportError(f"Module {name} has no Entry Point: moduleMain")
        moduleMain = module.moduleMain(
            framer, lambda msg: framer.helper.logger(name, msg)
        )

        # add module to framer
        setattr(moduleMain, "moduleInfo", module.moduleInfo)
        setattr(framer, name, moduleMain)
        return moduleMain

    # add lazy_load_module to framer
    framer.__getattr__ = lazy_load_module

    # if disable error hook
    if not hook_error:
        sys.excepthook = sys.__excepthook__

    # return framer
    init_logger("Framer Init Complete!")
    return framer
