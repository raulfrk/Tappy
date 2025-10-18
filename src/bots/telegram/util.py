from typing import Protocol, TypeGuard

from telegram import Chat, Message, Update


class EffectiveUserEssentials(Protocol):
    username: str
    id: int


class UpdateEssentials(Protocol):
    message: Message
    effective_user: EffectiveUserEssentials
    effective_chat: Chat


def valid_update(update: Update) -> TypeGuard[UpdateEssentials]:
    return not (
        update.effective_user is None
        or update.message is None
        or update.effective_user.username is None
        or update.effective_chat is None
    )
