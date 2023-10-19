import logging
import locale
import html
import json
import sys
import re

import pytz
import requests

import ScheduleAPI

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, ContextTypes, Defaults, CallbackQueryHandler
from telegram.constants import ParseMode

from datetime import date, timedelta, datetime
from typing import Optional, Tuple, Any

apiToken: Optional[str] = None


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


DEVELOPER_CHAT_ID: int = 558344464


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(str(context.error))}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привіт! Цей бот здатен відсилати розклад певної групи на певну дату.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Наявні команди: <code>/te</code>, <code>/te_t</code>")


async def send_schedule_message(update: Update, schedule_date: date) -> None:
    global apiToken
    api_result: requests.Response = ScheduleAPI.get_schedule_data(
        update.message.chat_id,
        schedule_date,
        apiToken
    )

    error: Optional[str] = ScheduleAPI.check_response_for_errors(api_result)
    if error is not None:
        await update.message.reply_text(error)
        return

    json_data: list[dict] = api_result.json()
    schedule: Optional[Tuple[str, list[list[InlineKeyboardButton]]]] = ScheduleAPI.check_response_for_multiple_groups(
        json_data,
        schedule_date
    )
    if schedule is not None:
        await update.message.reply_text(
            schedule[0],
            reply_markup=InlineKeyboardMarkup(schedule[1])
        )
        return

    schedule: Tuple[str, list[list[InlineKeyboardButton]]] = ScheduleAPI.convert_daydata_to_string(
        json_data[0],
        schedule_date
    )

    await update.message.reply_text(schedule[0], reply_markup=InlineKeyboardMarkup(schedule[1]))


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule_date: date = date.today()

    if len(context.args):
        matches: list[str] = re.findall(r'^(\d{1,2})\.(\d{1,2})$', context.args[0])
        if len(matches) != 1:
            await update.message.reply_text("Не вірні аргументи!")
            return
        try:
            schedule_date = date(schedule_date.year, int(matches[0][1]), int(matches[0][0]))
        except ValueError:
            await update.message.reply_text("Не вірні аргументи!")
            return

    await send_schedule_message(update, schedule_date)


async def tomorrow_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_schedule_message(update, date.today() + timedelta(hours=24))


async def update_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await button_belongs_to_user(update.callback_query):
        return

    callback_data: list[str] = update.callback_query.data.split("|")
    schedule_date: date = datetime.strptime(callback_data[1], "%d.%m.%Y")
    group_code: str = callback_data[2]
    show_name: bool = "SHOW_NAME" in callback_data

    global apiToken
    api_result: requests.Response = ScheduleAPI.get_schedule_data(
        update.callback_query.message.chat_id,
        schedule_date,
        apiToken
    )

    error: Optional[str] = ScheduleAPI.check_response_for_errors(api_result)
    if error is not None:
        await update.callback_query.answer(
            error,
            show_alert=True
        )
        return

    json_data: list[dict] = api_result.json()
    for group_data in json_data:
        if group_data["group"]["code"] == group_code:
            schedule: Tuple[str, list[list[InlineKeyboardButton]]] = ScheduleAPI.convert_daydata_to_string(
                group_data,
                schedule_date,
                show_name
            )
            await update.callback_query.edit_message_text(schedule[0], reply_markup=InlineKeyboardMarkup(schedule[1]))
            return

    await update.callback_query.answer(
        'Ця група вам не доступна!',
        show_alert=True
    )


async def button_belongs_to_user(query: CallbackQuery):
    if (query.message and
            query.message.reply_to_message and
            query.message.reply_to_message.from_user.id != query.from_user.id):
        await query.answer("Ця кнопка не належить вам!", show_alert=True)
        return False
    return True


def main() -> None:
    bot_token: str = sys.argv[1]

    locale.setlocale(locale.LC_ALL, 'uk_UA.UTF-8')

    if len(sys.argv) <= 2:
        print("No API token specified.")
    else:
        global apiToken
        apiToken = sys.argv[2]

    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        disable_web_page_preview=True,
        allow_sending_without_reply=False,
        tzinfo=pytz.timezone('Europe/Kiev')
    )

    application = Application.builder().token(bot_token).defaults(defaults).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("te", schedule_command))
    application.add_handler(CommandHandler("te_t", tomorrow_schedule_command))

    application.add_handler(CallbackQueryHandler(
        update_schedule_callback,
        pattern=r"^UPDATE_SCHEDULE\|\d{2}.\d{2}.\d{4}\|.*$"
    ))

    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
