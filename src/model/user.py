from pydantic import BaseModel, ConfigDict, Field


class UserModel(BaseModel):
    id: int | None = None


class TelegramUser(UserModel):
    telegram_id: int = Field(..., gt=0, description="Unique Telegram user ID")
    telegram_username: str | None = None
    telegram_chat_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


class TelegramUserCreate(UserModel):
    telegram_id: int
    telegram_username: str
    telegram_chat_id: int


class TelegramGroupedUser(TelegramUser):
    groups: list["GroupModel"] = []
    admin_of_groups: list["GroupModel"] = []


class GroupModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    name: str
    admins: list[TelegramUser] = []
    users: list[TelegramUser] = []
