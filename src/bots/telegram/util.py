import functools
import typing
from typing import TYPE_CHECKING, Protocol, TypeGuard

from loguru import logger
from telegram import Chat, Message, Update

if TYPE_CHECKING:
    from loguru import Logger


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


F = typing.TypeVar("F", bound=typing.Callable[..., typing.Awaitable[typing.Any]])


def log_enriched(func: F) -> F:
    @functools.wraps(func)
    async def wrapper(
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.Any:
        update: Update = args[0]
        message_id: int = update.message.message_id  # type: ignore[union-attr]
        log: "Logger" = logger.bind(
            user_id=update.effective_user.id if update.effective_user else None,
            username=update.effective_user.username if update.effective_user else None,
            chat_id=update.effective_chat.id if update.effective_chat else None,
            message_id=message_id,
        )
        text: str = update.message.text or ""  # type: ignore[union-attr]
        date = update.message.date  # type: ignore[union-attr]

        log.info("handling command", text=text, date=date)

        result = await func(*args, log, **kwargs)
        log.info("handling command completed", message_id=message_id, text=text)
        return result

    return typing.cast(F, wrapper)
