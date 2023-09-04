import re
from typing import Tuple
from datetime import datetime, time, timedelta
from Teacher import Teacher
import pytz


class Lesson:
    __slots__ = ["local_id", "names", "lesson_type", "teachers", "comment", "place", "begin_time", "duration"]
    local_id: str
    names: Tuple[str, str]
    lesson_type: str
    teachers: list[Teacher]
    comment: str
    place: str
    begin_time: time
    duration: timedelta

    def __init__(self, data: dict):
        self.local_id = data["local_id"]
        self.names = (data["names"][0], data["names"][1])

        match data["lesson_type"]:
            case "lecture":
                self.lesson_type = "Лекція"
            case "practical":
                self.lesson_type = "Практична"
            case "laboratory":
                self.lesson_type = "Лабораторна"
            case _:
                self.lesson_type = data["lesson_type"]

        self.teachers = []
        for teacher_data in data["lecturers"]:
            self.teachers.append(Teacher(teacher_data))
        self.comment = data["comment"]
        self.places.append((data["places"][0][0], data["places"][0][1]))

        minutes_since_midnight: int = int(data["time"])
        self.begin_time = time(
            hour=(minutes_since_midnight // 60),
            minute=(minutes_since_midnight % 60),
            tzinfo=pytz.timezone('Europe/Kiev')
        )

        self.duration = timedelta(minutes=int(data["duration"]))

    def get_telegram_message(self) -> str:
        result: str = f'<u>{self.begin_time.strftime("%H:%M")} - '
        result += (datetime.combine(datetime.now(), self.begin_time) + self.duration).strftime("%H:%M")
        result += f'</u> | {self.names[0]} | {self.lesson_type} | {self.teachers[0]} | '
        if re.match(r'', self.place):
            result += f'<a href="{self.place}">Посилання</a>'
        else:
            map_url: str = 'https://www.google.com/maps/d/u/4/edit?mid=1q08ygA-JJCaMu0LrBQxZiJ1fxVq8KD0&usp=sharing'
            result += f'<a href="{map_url}">{self.place}</a>'

        if len(self.comment) != 0:
            result += f' // {self.comment}'

        return result
