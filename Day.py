from typing import Optional
from datetime import date
from Lesson import Lesson


class Day:
    __slots__ = ["first_subgroup", "second_subgroup", "day_date", "week_number"]
    first_subgroup: list[Lesson]
    second_subgroup: Optional[list[Lesson]]
    day_date: date
    week_number: int

    def __init__(self, data: dict, our_date: date):
        self.day_date = our_date
        self.week_number = data["week_number"]

        self.first_subgroup = []
        for lesson_data in data["first_subgroup"]:
            self.first_subgroup.append(Lesson(lesson_data))

        self.second_subgroup = None
        if data["second_subgroup"]:
            self.second_subgroup = []
            for lesson_data in data["second_subgroup"]:
                self.second_subgroup.append(Lesson(lesson_data))

    def get_telegram_message(self) -> str:
        if not len(self.first_subgroup) and (not self.second_subgroup or not len(self.second_subgroup)):
            return f'{self.day_date.strftime("%d.%m")} ніяких пар немає!'
        result: str = f'<b>Пари на {self.day_date.strftime("%d.%m")} '
        result += f'({self.day_date.strftime("%A").capitalize()} {self.week_number}):</b>\n\n'
        result += '<b>Перша підгрупа:</b>\n'

        nums_dict: dict[str, str] = {
            "0": "0️⃣",
            "1": "1️⃣",
            "2": "2️⃣",
            "3": "3️⃣",
            "4": "4️⃣",
            "5": "5️⃣",
            "6": "6️⃣",
            "7": "7️⃣",
            "8": "8️⃣",
            "9": "9️⃣"
        }

        lesson: Lesson
        for index, lesson in enumerate(self.first_subgroup):
            for num in str(index + 1):
                result += nums_dict[num]
            result += f' | {lesson.get_telegram_message()}\n'

        if self.second_subgroup is None:
            return result

        result += '\n<b>Друга підгрупа:</b>\n'
        for index, lesson in enumerate(self.second_subgroup):
            for num in str(index + 1):
                result += nums_dict[num]
            result += f' | {lesson.get_telegram_message()}\n'

        return result
