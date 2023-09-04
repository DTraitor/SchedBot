from typing import Tuple


class Group:
    __slots__ = ["code", "names", "desc"]
    code: str
    names: Tuple[str, str]
    desc: str

    def __init__(self, data: dict):
        self.code = data["code"]
        self.names = (data["names"][0], data["names"][1])
        self.desc = data["desc"]
