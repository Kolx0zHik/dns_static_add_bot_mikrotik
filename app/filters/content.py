from aiogram.filters import BaseFilter
from aiogram.types import Message

MAX_TEXT_MESSAGE_LENGTH = 3500


class TextMessageFilter(BaseFilter):
    """Allow only non-empty text messages with bounded length."""

    def __init__(self, max_length: int = MAX_TEXT_MESSAGE_LENGTH) -> None:
        self._max_length = max_length

    async def __call__(self, message: Message) -> bool:
        text = message.text
        return text is not None and text.strip() != "" and len(text.strip()) <= self._max_length
