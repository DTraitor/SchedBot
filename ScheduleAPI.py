from telegram import InlineKeyboardButton
from typing import Optional, Tuple
from datetime import date, timedelta
from Day import Day
from Group import Group
import requests


def make_api_get_request(url_path: str, data: dict) -> requests.Response:
    return requests.get("https://api.crwnd.dev/schedule/violet" + url_path, data)


def get_schedule_data(
    telegram_id: int,
    schedule_date: date,
    token: Optional[str]
) -> requests.Response:
    return make_api_get_request('/scheduleBySubgroupsTg', {
        "telegram_id": telegram_id,
        "year": schedule_date.year,
        "month": schedule_date.month,
        "day": schedule_date.day,
        "show_place": "false" if token is None else "true",
        "token": token
    })


def check_response_for_errors(response: requests.Response) -> Optional[str]:
    if response.status_code == 200:
        return None
    match response.json()["error"]:
        case "users and groups not found" | "groups not found":
            return "Нажаль, пов'язаних з цим чатом студентських груп знайдено не було 😔"
        case _:
            return "Щось пішло не так 🕯"


def check_response_for_multiple_groups(
        response_data: list[dict],
        schedule_date: date
) -> Optional[Tuple[str, list[list[InlineKeyboardButton]]]]:

    if len(response_data) <= 1:
        return None

    keyboard: list[list[InlineKeyboardButton]] = [[]]
    group_data: dict
    for group_data in response_data:
        if len(keyboard[-1]) >= 3:
            keyboard.append([])
        group: Group = Group(group_data["group"])
        keyboard[-1].append(InlineKeyboardButton(
            group.name,
            callback_data=f'UPDATE_SCHEDULE|{schedule_date.strftime("%d.%m.%Y")}|{group.code}'
        ))

    return "До цього чату прив'язано декілька груп. Оберіть потрібну:", keyboard


def convert_daydata_to_string(
        data: dict,
        schedule_date: date
) -> Tuple[str, list[list[InlineKeyboardButton]]]:

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Попередній день",
                callback_data=
                f"UPDATE_SCHEDULE|{(schedule_date - timedelta(hours=24)).strftime('%d.%m.%Y')}|{data['group']['code']}"
            ),
            InlineKeyboardButton(
                "Наступний день ➡️",
                callback_data=
                f"UPDATE_SCHEDULE|{(schedule_date + timedelta(hours=24)).strftime('%d.%m.%Y')}|{data['group']['code']}"
            )
        ]
    ]

    return Day(data, schedule_date).get_telegram_message(), keyboard
