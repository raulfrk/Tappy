from pydantic import BaseModel, ConfigDict, Field


class UserModel(BaseModel):
    id: int | None = None


class TelegramUser(UserModel):
    telegram_id: int = Field(..., gt=0, description="Unique Telegram user ID")
    model_config = ConfigDict(from_attributes=True)


class TelegramGroupedUser(TelegramUser):
    groups: list["GroupModel"] = []
    admin_of_groups: list["GroupModel"] = []


class GroupModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    name: str
    admins: list[TelegramUser] = []
    users: list[TelegramUser] = []
