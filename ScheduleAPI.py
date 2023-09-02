from typing import Optional
from datetime import date
from Day import Day
import requests


def make_api_get_request(url_path: str, data: dict) -> requests.Response:
    return requests.get("https://api.crwnd.dev/schedule/violet" + url_path, data)


def get_schedule_message(
        schedule_date: date,
        telegram_id: Optional[int],
        token: Optional[str]
) -> str:
    result: requests.Response = make_api_get_request("/scheduleBySubgroups", {
        "group_code": "se-224b",
        #"telegram_id": telegram_id,
        "year": schedule_date.year,
        "month": schedule_date.month,
        "day": schedule_date.day,
        "show_place": "false" if token is None else "true",
        "token": token
    })

    # if everything is fine

    return Day(result.json(), schedule_date).get_telegram_message()
