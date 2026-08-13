from aiogram.filters import BaseFilter
from aiogram.types import Message


class TextMessageFilter(BaseFilter):
    """Allow only non-empty text messages with bounded length."""

    def __init__(self, max_length: int = 253) -> None:
        self._max_length = max_length

    async def __call__(self, message: Message) -> bool:
        text = message.text
        return text is not None and text.strip() != "" and len(text.strip()) <= self._max_length
