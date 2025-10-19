"""Pydantic types and helpers for Telegram user/group models.
Note: use default_factory=list for per-instance mutable defaults.

These models are used for runtime state management and data validation,
not for database persistence (see src/db/schema.py for that).

The general workflow is to map the resulting models from the database
ORM models to these Pydantic models for use in the application logic.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserModel(BaseModel):
    """Base user model with common fields."""

    id: int | None = None


class TelegramUser(UserModel):
    """Telegram user model with Telegram-specific fields.
    Note: This has no group relationships, use TelegramGroupedUser for that.
    """

    telegram_id: int = Field(..., gt=0, description="Unique Telegram user ID")
    telegram_username: str | None = None
    telegram_chat_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


class TelegramUserCreate(UserModel):
    """Model for creating a new Telegram user."""

    telegram_id: int
    telegram_username: str
    telegram_chat_id: int


class TelegramGroupedUser(TelegramUser):
    """Telegram user model with group relationships and refs."""

    groups: list["GroupModel"] = []
    admin_of_groups: list["GroupModel"] = []


class GroupModel(BaseModel):
    """Group model with user relationships.
    Note: admins and users are lists of TelegramUser models which do not
    have group relationships to avoid circular references.
    """

    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    name: str
    admins: list[TelegramUser] = []
    users: list[TelegramUser] = []
