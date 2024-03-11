from dataclasses import dataclass

@dataclass
class Test:
    name: str = ""
    phones: list = []
    friends: dict = {}
    family: set = set()
