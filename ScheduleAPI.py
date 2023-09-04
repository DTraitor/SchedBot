from telegram import InlineKeyboardButton
from typing import Optional, Tuple
from datetime import date, timedelta
from Day import Day
from Group import Group
import requests


def make_api_get_request(url_path: str, data: dict) -> requests.Response:
    return requests.get("https://api.crwnd.dev/schedule/violet" + url_path, data)


def get_schedule_message(
        schedule_date: date,
        telegram_id: Optional[int],
        group_code: Optional[str],
        token: Optional[str]
) -> Tuple[str, list[list[InlineKeyboardButton]]]:

    url_link: str = "/scheduleBySubgroupsTg" if telegram_id is not None else "/scheduleBySubgroups"
    result: requests.Response = make_api_get_request(url_link, {
        "group_code": group_code,
        "telegram_id": telegram_id,
        "year": schedule_date.year,
        "month": schedule_date.month,
        "day": schedule_date.day,
        "show_place": "false" if token is None else "true",
        "token": token
    })

    if result.status_code != 200:
        match result.content:
            case "users and groups not found" | "groups not found":
                return "Нажаль, пов'язаних з цим чатом студентських груп знайдено не було 😔", True
            case _:
                return "Щось пішло не так 🕯", []

    result_data: list[dict] = result.json()
    keyboard: list[list[InlineKeyboardButton]]

    if len(result_data) > 1:
        keyboard = [[]]
        group_data: dict
        for group_data in result_data:
            if len(keyboard[-1]) >= 3:
                keyboard.append([])
            group: Group = Group(group_data["group"])
            keyboard[-1].append(InlineKeyboardButton(
                group.names[0],
                callback_data=f'CHOOSEGROUP|{schedule_date.strftime("%d.%m.%Y")}|{group.code}'
            ))

        return "До цього чату прив'язано декілька груп. Оберіть потрібну:", keyboard
    return process_schedule_data(result_data[0], group_code, schedule_date)


def process_schedule_data(
        data: dict,
        group_code: Optional[str],
        schedule_date: date
) -> Tuple[str, list[list[InlineKeyboardButton]]]:

    if group_code is None:
        group_code = dict[0]["group"]["code"]

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Попередній день",
                callback_data=f"SWITCHTABLE|{(schedule_date - timedelta(hours=24)).strftime('%d.%m.%Y')}|{group_code}"
            ),
            InlineKeyboardButton(
                "Наступний день ➡️",
                callback_data=f"SWITCHTABLE|{(schedule_date + timedelta(hours=24)).strftime('%d.%m.%Y')}|{group_code}"
            )
        ]
    ]

    return Day(data, schedule_date).get_telegram_message(), keyboard
