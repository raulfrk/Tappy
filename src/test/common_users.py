from src.model.user import TelegramUserCreate

admin_user_create = TelegramUserCreate(
    telegram_id=1, telegram_username="adminuser", telegram_chat_id=1
)
target_user_create = TelegramUserCreate(
    telegram_id=2, telegram_username="targetuser", telegram_chat_id=2
)
outsider_user_create = TelegramUserCreate(
    telegram_id=3, telegram_username="outsideruser", telegram_chat_id=3
)
other_admin_user_create = TelegramUserCreate(
    telegram_id=4, telegram_username="otheradminuser", telegram_chat_id=4
)
outsider_admin_user_create = TelegramUserCreate(
    telegram_id=5, telegram_username="outsideradminuser", telegram_chat_id=5
)
regular_user_create = TelegramUserCreate(
    telegram_id=6, telegram_username="regularminuser", telegram_chat_id=6
)
