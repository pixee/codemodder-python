from abc import ABC
from dataclasses import dataclass


@dataclass
class ABCDataclass(ABC):
    """Inspired by https://stackoverflow.com/a/60669138"""

    def __new__(cls, *args, **kwargs):
        del args, kwargs
        if cls == ABCDataclass or cls.__bases__[0] == ABCDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)
