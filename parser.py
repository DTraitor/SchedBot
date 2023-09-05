from typing import Tuple

import tabula
import pandas
import re


class Lesson:
    __slots__ = ["name", "lesson_type", "teacher_type", "teacher", "place", "subgroup", "week", "day", "lesson_number"]
    name: str
    lesson_type: str
    teacher_type: str
    teacher: str
    place: str
    subgroup: int
    week: int
    day: int
    lesson_number: int

    def __init__(self):
        # Default value
        self.subgroup = 0


class APILesson:
    __slots__ = [
        "group_code",
        "time",
        "day_number",
        "week_number",
        "start_date",
        "end_date",
        "template",
        "lecturers",
        "names",
        "comment",
        "duration",
        "place",
        "lesson_type",
        "recordings",
        "subgroup"
    ]
    group_code: str
    time: int
    day_number: int
    week_number: int
    start_date: list[int]
    end_date: list[int]
    template: str
    lecturers: list[str]
    names: list[str]
    comment: str
    duration: int
    place: str
    lesson_type: str
    recordings: list[str]
    subgroup: int


def schedule_pdf_to_list(filepath: str, pages: range) -> list[APILesson]:
    # Read pdf into list of DataFrame
    dfs = tabula.read_pdf(filepath, pages='all', lattice=True)

    lessons_list: list[list[Lesson]] = []

    page: pandas.DataFrame
    lesson: Lesson
    lesson_data: Tuple
    column: Tuple[int, pandas.Series]
    for index, page in enumerate(dfs):
        if pages is not None and index not in pages:
            continue
        lessons_list.append([])
        for lesson_num in range(0, 36):
            lesson = Lesson()
            lesson.lesson_number = lesson_num % 6
            lessons_list[-1].append(lesson)

        # iterate over columns of the page
        row: pandas.Series
        for row in page.itertuples():
            if row.Index < 2:
                continue
            for ind, value in enumerate(row):
                if (ind not in range(3, 7)) or pandas.isna(value):
                    continue
                matches = re.findall(
                    # Хай горить в аду, той хто робив цей розклад і додумався пихати латинські букви в українські слова
                    r"^(.*?)\r?(\d{1,2}\. \d{3}\w?)?\r?(Л(?:а|a)б(?:о|o)(?:р|p)(?:а|a)т(?:о|o)(?:р|p)н(?:а|a)|П(?:р|p)(?:а|a)ктичн(?:е|e)|Л(?:е|e)кц(?:і|i)я)\r?(.*?)\r?([A-ZА-ЯІЇЄ].*? .?\..?\.)$",
                    value
                )
                if len(matches):
                    lesson = Lesson()
                    lesson.name = matches[0][0]
                    lesson.place = matches[0][1] if matches[0][1] is not None else "Відсутнє"
                    lesson.lesson_type = matches[0][2]
                    lesson.teacher_type = matches[0][3]
                    lesson.teacher = matches[0][4]
                    lesson.subgroup = 1 if ind <= 3 else 2
                    lesson.week = 1 if index % 2 == 0 else 2
                    lesson.day = (row.Index - 2) // 6
                    lesson.lesson_number = (row.Index - 2) % 6
                    lessons_list[-1].append(lesson)
                else:
                    lesson = lessons_list[-1][row.Index - 2]
                    match ind:
                        case 3:
                            lesson.name = value
                            lesson.week = 1 if index % 2 == 0 else 2
                            lesson.day = (row.Index - 2) // 6
                            lesson.lesson_number = (row.Index - 2) % 6
                        case 4:
                            lesson.place = value
                        case 5:
                            data = value.split('\r')
                            lesson.lesson_type = data[0]
                            lesson.teacher_type = data[1]
                        case 6:

                            lesson.teacher = value

    # merge all lists into one if lesson has attribute name
    computed_lessons_list: list[Lesson] = [
        lesson for lessons in lessons_list for lesson in lessons if hasattr(lesson, "name")
    ]

    has_subgroups: bool = False

    for lesson in computed_lessons_list:
        lesson.lesson_type = lesson.lesson_type.replace('a', 'а').replace('o', 'о').replace('і', 'i').replace('e', 'е').\
            replace('p', 'р')
        lesson.place = lesson.place.replace(' ', '')
        lesson.teacher_type.strip()
        # Fix for the teacher type. Just in case
        if re.match(r'^Проф', lesson.teacher_type):
            lesson.teacher_type = "Професор"
        elif re.match(r'^Доц', lesson.teacher_type):
            lesson.teacher_type = "Доцент"
        elif re.match(r'^Старш', lesson.teacher_type):
            lesson.teacher_type = "Старший викладач"
        elif re.match(r'^Асист', lesson.teacher_type):
            lesson.teacher_type = "Асистент"
        if lesson.subgroup != 0:
            has_subgroups = True

    api_lessons_list: list[APILesson] = []

    for lesson in computed_lessons_list:
        api_lesson: APILesson = APILesson()
        # Gotta change this
        api_lesson.group_code = "ІП-94"
        match lesson.lesson_number:
            case 0:
                api_lesson.time = 480
            case 1:
                api_lesson.time = 590
            case 2:
                api_lesson.time = 700
            case 3:
                api_lesson.time = 810
            case 4:
                api_lesson.time = 920
            case 5:
                api_lesson.time = 1030
        api_lesson.day_number = lesson.day
        api_lesson.week_number = lesson.week
        api_lesson.start_date = [2023, 9, 1]
        api_lesson.end_date = [2023, 12, 22]
        # Gotta change this
        api_lesson.template = "1"
        # Gotta change this
        api_lesson.lecturers = [lesson.teacher]
        # Check if it's an english name
        if re.match(r'^(?:[A-z]|\s)*$', lesson.name[0]):
            api_lesson.names = ["", lesson.name]
        else:
            api_lesson.names = [lesson.name, ""]
        api_lesson.comment = ""
        api_lesson.duration = 90
        api_lesson.place = lesson.place
        api_lesson.lesson_type = lesson.lesson_type
        api_lesson.recordings = []
        api_lesson.subgroup = lesson.subgroup if has_subgroups else -1
        api_lessons_list.append(api_lesson)

    return api_lessons_list
