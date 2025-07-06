import io
import typing


class CustomStdout(io.TextIOBase):
    def __init__(self, custom_output_handler: typing.Callable[[str], None]):
        super().__init__()
        self.custom_output_handler = custom_output_handler

    def write(self, text: str) -> int:
        self.custom_output_handler(text)
        return len(text)
