from telegram import Update
from telegram.ext import ContextTypes

from src.bots.telegram.util import valid_update
from src.db.connection import get_session
from src.model.user import TelegramUserCreate
from src.services.telegram_user import TelegramUserService


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not valid_update(update):
        raise Exception("Invalid update", update.to_dict())
    session = get_session()

    ts_service = TelegramUserService(session)
    potential_user = ts_service.get_grouped_user(telegram_id=update.effective_user.id)
    user_create = TelegramUserCreate(
        telegram_id=update.effective_user.id,
        telegram_username=update.effective_user.username,
        telegram_chat_id=update.effective_chat.id,
    )
    user = ts_service.create_user(user_create)
    session.close()
    if potential_user is None:
        await update.message.reply_text(
            f"Hello, welcome new user @{user.telegram_username}!"
        )
    else:
        await update.message.reply_text(
            "Hello, welcome back " f"@{user.telegram_username}!"
        )
