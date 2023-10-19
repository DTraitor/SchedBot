import re
from typing import Tuple
from datetime import datetime, time, timedelta
from Teacher import Teacher
import pytz


class Lesson:
    __slots__ = ["local_id", "name", "lesson_type", "teachers", "comment", "place", "begin_time", "duration", "canceled"]
    local_id: str
    name: str
    lesson_type: str
    teachers: list[Teacher]
    comment: str
    place: str
    begin_time: time
    duration: timedelta
    canceled: bool

    def __init__(self, data: dict):
        self.local_id = data["local_id"]

        self.name = data["names"][0]

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
        self.place = data["place"]

        minutes_since_midnight: int = int(data["time"])
        self.begin_time = time(
            hour=(minutes_since_midnight // 60),
            minute=(minutes_since_midnight % 60),
            tzinfo=pytz.timezone('Europe/Kiev')
        )

        self.duration = timedelta(minutes=int(data["duration"]))
        self.canceled = data["canceled"]

    def get_telegram_message(self) -> str:
        result: str = f'{self.begin_time.strftime("%H:%M")} - '
        result += (datetime.combine(datetime.now(), self.begin_time) + self.duration).strftime("%H:%M")
        result += f' | '
        if self.canceled:
            result += '<s>'
        result += f'{self.name} | {self.lesson_type} | {self.teachers[0]} | '
        if re.match(r'^https:\/\/', self.place):
            result += f'<a href="{self.place}">Посилання</a>'
        else:
            map_url: str = 'https://www.google.com/maps/d/u/4/edit?mid=1q08ygA-JJCaMu0LrBQxZiJ1fxVq8KD0&usp=sharing'
            result += f'<a href="{map_url}">{self.place}</a>'

        if self.canceled:
            result += '</s>'

        if len(self.comment) != 0:
            result += f' // {self.comment}'

        return result
