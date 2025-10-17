from telegram import Update
from telegram.ext import ContextTypes

from src.db.connection import get_session
from src.services.telegram_user import TelegramUserService


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (
        update.effective_user is None
        or update.message is None
        or update.effective_user.username is None
    ):
        return
    session = get_session()

    ts_service = TelegramUserService(session)
    potential_user = ts_service.get_grouped_user(telegram_id=update.effective_user.id)

    user = ts_service.create_user(
        telegram_id=update.effective_user.id,
        telegram_username=update.effective_user.username,
    )
    session.close()
    if potential_user is None:
        await update.message.reply_text(
            f"Hello, welcome new user @{user.telegram_username}!"
        )
    else:
        await update.message.reply_text(
            "Hello, welcome back " f"@{user.telegram_username}!"
        )
