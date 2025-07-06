import os
import textwrap
import time

_TERMINAL_MAX_WIDTH = 0


def _format_with_wrap(msg: str, width: int) -> str:
    result = []
    for line in msg.splitlines(keepends=True):
        if len(line.strip()) == 0 or len(line) <= width:
            result.append(line)
        else:
            wrapped_lines = textwrap.wrap(
                line, width=width, break_long_words=True, replace_whitespace=False
            )
            result.extend([l + "\n" for l in wrapped_lines])
    return "".join(result)


def _get_terminal_width() -> int:
    global _TERMINAL_MAX_WIDTH

    if _TERMINAL_MAX_WIDTH == 0:
        try:
            columns = os.get_terminal_size().columns - 2
            _TERMINAL_MAX_WIDTH = columns

        except (AttributeError, OSError):
            _TERMINAL_MAX_WIDTH = 80

    return _TERMINAL_MAX_WIDTH


def logger(from_module: str, message: str) -> None:
    max_width = _get_terminal_width()
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    message = _format_with_wrap(str(message), width=max_width)

    print(f"* {from_module} ({current_time})")
    print("|", "\n| ".join(message.split("\n")), "\n")
    return
