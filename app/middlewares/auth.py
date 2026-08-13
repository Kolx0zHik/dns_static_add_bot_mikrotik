from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class AllowedUsersMiddleware(BaseMiddleware):
    """Reject updates from Telegram users outside the allow list."""

    def __init__(self, allowed_users: frozenset[int]) -> None:
        self._allowed_users = allowed_users

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        user_id = getattr(user, "id", None)

        if user_id in self._allowed_users:
            logger.info("Allowed user action telegram_id=%s", user_id)
            return await handler(event, data)

        logger.warning("Denied user action telegram_id=%s", user_id)
        if isinstance(event, Message):
            await event.answer("Доступ запрещён.")
        elif isinstance(event, CallbackQuery):
            await event.answer("Доступ запрещён.", show_alert=True)
        return None
