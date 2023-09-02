import traceback
import logging
import locale
import html
import json
import sys
import re

import pytz

import ScheduleAPI

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, ContextTypes, Defaults, CallbackQueryHandler
from telegram.constants import ParseMode

from datetime import date, timedelta, datetime
from typing import Optional, Tuple

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
        f"<pre>{html.escape(context.error)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привіт! Цей бот здатен відсилати розклад певної групи на певну дату.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Наявні команди: <code>/te</code>, <code>/te_t</code>")


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

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Попередній день",
                callback_data=f"SWITCH_TIMETABLE|{(schedule_date - timedelta(hours=24)).strftime('%d.%m.%Y')}"
            ),
            InlineKeyboardButton(
                "Наступний день ➡️",
                callback_data=f"SWITCH_TIMETABLE|{(schedule_date + timedelta(hours=24)).strftime('%d.%m.%Y')}"
            )
        ]
    ]

    global apiToken
    api_result: Tuple[str, bool] = ScheduleAPI.get_schedule_message(schedule_date, update.message.chat_id, apiToken)

    if api_result[1]:
        await update.message.reply_text(api_result[0])
    else:
        await update.message.reply_text(api_result[0], reply_markup=InlineKeyboardMarkup(keyboard))


async def tomorrow_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule_date: date = date.today() + timedelta(hours=24)

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Попередній день",
                callback_data=f"SWITCH_TIMETABLE|{(schedule_date - timedelta(hours=24)).strftime('%d.%m.%Y')}"
            ),
            InlineKeyboardButton(
                "Наступний день ➡️",
                callback_data=f"SWITCH_TIMETABLE|{(schedule_date + timedelta(hours=24)).strftime('%d.%m.%Y')}"
            )
        ]
    ]

    global apiToken
    await update.message.reply_text(
        ScheduleAPI.get_schedule_message(schedule_date, update.message.chat_id, apiToken),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def schedule_change_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await button_belongs_to_user(update.callback_query):
        return

    schedule_date = datetime.strptime(update.callback_query.data.split("|", 2)[1], "%d.%m.%Y")
    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Попередній день",
                callback_data=f"SWITCH_TIMETABLE|{(schedule_date - timedelta(hours=24)).strftime('%d.%m.%Y')}"
            ),
            InlineKeyboardButton(
                "Наступний день ➡️",
                callback_data=f"SWITCH_TIMETABLE|{(schedule_date + timedelta(hours=24)).strftime('%d.%m.%Y')}"
            )
        ]
    ]

    global apiToken
    await update.callback_query.edit_message_text(
        ScheduleAPI.get_schedule_message(schedule_date, update.callback_query.message.chat_id, apiToken),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_belongs_to_user(query: CallbackQuery):
    if (query.message and
            query.message.reply_to_message and
            query.message.reply_to_message.from_user.id != query.from_user.id):
        await query.answer("Ця кнопка не належить вам!", show_alert=True)
        return False
    return True


def main() -> None:
    if len(sys.argv) <= 1:
        print("No bot token specified. Please provide BOT_TOKEN environment variable.")
        return
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
        tzinfo=pytz.timezone('Europe/Kiev'),
        protect_content=True
    )

    application = Application.builder().token(bot_token).defaults(defaults).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("te", schedule_command))
    application.add_handler(CommandHandler("te_t", tomorrow_schedule_command))

    application.add_handler(CallbackQueryHandler(
        schedule_change_callback,
        pattern=r"^SWITCH_TIMETABLE\|\d{2}.\d{2}.\d{4}$"
    ))

    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
