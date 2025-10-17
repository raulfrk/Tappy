from typing import Any, cast

import pytest
from telegram import Update

from src.bots.telegram.flows.start import start
from src.test.telegram.conftest import MakeUpdate, SentMessages


@pytest.mark.asyncio
async def test_application_handles_start(
    make_update: MakeUpdate,
    fake_context: Any,
    sent: SentMessages,
) -> None:
    update = cast(
        Update,
        make_update(
            text="/start",
            effective_user_id=1234,
            effective_user_username="User",
            chat_id=1,
        ),
    )
    await start(update, fake_context)
    assert sent.replies and "Hello, welcome new user @User!" in sent.replies[0]["text"]

    await start(update, fake_context)
    assert sent.replies and "Hello, welcome back @User!" in sent.replies[1]["text"]

    update = cast(
        Update,
        make_update(
            text="/start",
            effective_user_id=1234,
            effective_user_username="User2",
            chat_id=1,
        ),
    )
    await start(update, fake_context)
    assert sent.replies and "Hello, welcome back @User2!" in sent.replies[2]["text"]
