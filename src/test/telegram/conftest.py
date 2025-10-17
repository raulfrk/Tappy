# conftest.py (or wherever your fixtures live)
from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Protocol

import pytest
from sqlalchemy.orm import Session


@pytest.fixture(scope="function", autouse=True)
def inject_config(db: Session, pg_url: str) -> None:
    """Set up a PostgreSQL test container and provide the database URL."""
    import src.config as cfg

    cfg.config = cfg.Config(database_url=pg_url)


# ---- Generic message capture -------------------------------------------------


@dataclass
class SentMessages:
    # Store arbitrary key/values coming from **kwargs; keep it simple for tests
    replies: list[dict[str, Any]] = field(default_factory=list)  # reply_text calls
    bot_sends: list[dict[str, Any]] = field(default_factory=list)  # bot.send_message
    edits: list[dict[str, Any]] = field(default_factory=list)  # edit_text calls

    async def reply_text(self, text: str, **kwargs: Any) -> None:
        self.replies.append({"text": text, **kwargs})

    async def edit_text(self, text: str, **kwargs: Any) -> None:
        self.edits.append({"text": text, **kwargs})

    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> None:
        self.bot_sends.append({"chat_id": chat_id, "text": text, **kwargs})


@pytest.fixture
def sent() -> SentMessages:
    return SentMessages()


# ---- Factories to build fake Telegram objects --------------------------------


class MakeMessage(Protocol):
    def __call__(self, *, text: str | None, chat_id: int) -> SimpleNamespace: ...


@pytest.fixture
def make_message(sent: SentMessages) -> MakeMessage:
    """
    Factory: create a minimal Message-like object with .text, .reply_text, .edit_text.
    """

    def _make_message(
        *, text: str | None = None, chat_id: int = 123
    ) -> SimpleNamespace:
        return SimpleNamespace(
            message_id=1,
            text=text,
            chat=SimpleNamespace(id=chat_id),
            reply_text=sent.reply_text,
            edit_text=sent.edit_text,
        )

    return _make_message


class MakeUpdate(Protocol):
    def __call__(
        self,
        *,
        text: str | None,
        chat_id: int,
        effective_user_id: int,
        effective_user_username: str,
    ) -> SimpleNamespace: ...


@pytest.fixture
def make_update(make_message: MakeMessage) -> MakeUpdate:
    """
    Factory: create a minimal Update-like object with .message and .effective_user.
    """

    def _make_update(
        *,
        text: str | None = None,
        chat_id: int = 123,
        effective_user_id: int = 42,
        effective_user_username: str = "tester",
    ) -> SimpleNamespace:
        msg = make_message(text=text, chat_id=chat_id)
        return SimpleNamespace(
            update_id=999,
            message=msg,
            effective_chat=msg.chat,
            effective_user=SimpleNamespace(
                id=effective_user_id, username=effective_user_username
            ),
        )

    return _make_update


# ---- Fake context/bot --------------------------------------------------------


@pytest.fixture
def fake_context(sent: SentMessages) -> SimpleNamespace:
    """
    Minimal Context-like object exposing .bot.send_message and .args.
    """
    bot = SimpleNamespace(send_message=sent.send_message)
    return SimpleNamespace(
        bot=bot,
        args=[],
        chat_data={},
        user_data={},
        application=SimpleNamespace(),
    )


# ---- Optional: time freezer for deterministic tests -------------------------


@pytest.fixture
def freeze_time(monkeypatch: Any) -> bool:
    """
    Patch any time function you use (datetime.utcnow, asyncio.sleep, etc.).
    """
    import asyncio

    async def fast_sleep(_secs: float) -> None:  # avoid real delays
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep, raising=True)
    return True
