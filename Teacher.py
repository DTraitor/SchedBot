class Teacher:
    __slots__ = ["code", "name", "surname", "patronymic"]
    code: str
    name: str
    surname: str
    patronymic: str

    def __init__(self, data: dict):
        self.code = data["code"]
        self.name = data["name"]
        self.surname = data["surname"]
        self.patronymic = data["patronymic"]

    def __str__(self):
        return self.surname + ' ' + self.name[0] + '.' + self.patronymic[0] + '.'
