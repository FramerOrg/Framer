def logger(from_module: str, message: str, max_width: int = None):
    import time

    def format_with_wrap(msg: str, width: int):
        import textwrap

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

    def get_terminal_width():
        import os

        try:
            columns = os.get_terminal_size().columns - 2
            return columns
        except (AttributeError, OSError):
            return 80

    if max_width is None:
        max_width = get_terminal_width()

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # if message only one line
    if "\n" not in message:
        print(f"* {from_module} ({current_time}) {message}")
        return

    # if message multiple lines
    if "\n" in message:
        message = format_with_wrap(message, width=max_width)
        print(f"* {from_module} ({current_time})")
        print("|", "\n| ".join(message.split("\n")), "\n")
        return


def global_except_hook(exc_type, exc_value, exc_traceback):
    import sys
    import traceback

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger(
        "ErrHooker",
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
    )
