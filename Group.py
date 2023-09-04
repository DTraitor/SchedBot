from typing import Tuple


class Group:
    __slots__ = ["code", "name", "desc"]
    code: str
    names: str
    desc: str

    def __init__(self, data: dict):
        self.code = data["code"]
        self.name = data["names"][0]
        self.desc = data["desc"]
