from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import cast

from aiogram.types import Message

from app.filters.content import MAX_TEXT_MESSAGE_LENGTH, TextMessageFilter


def _message(text: str | None) -> Message:
    return cast(Message, SimpleNamespace(text=text))


def test_text_message_filter_accepts_multiline_domain_list() -> None:
    result = asyncio.run(TextMessageFilter()(_message("example.com\nsub.example.com")))

    assert result is True


def test_text_message_filter_rejects_oversized_list() -> None:
    result = asyncio.run(TextMessageFilter()(_message("a" * (MAX_TEXT_MESSAGE_LENGTH + 1))))

    assert result is False
