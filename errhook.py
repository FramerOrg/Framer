import traceback
from .logger import logger


def global_except_hook(exc_type, exc_value, exc_traceback) -> None:
    logger(
        "ErrHooker",
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
    )
