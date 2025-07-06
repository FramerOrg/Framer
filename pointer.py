import types


class Pointer(types.ModuleType):
    def __init__(self, **kwargs):
        super().__init__("Pointer")
        self.__dict__.update(kwargs)
