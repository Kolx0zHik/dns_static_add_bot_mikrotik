from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import RouterCatalog, load_settings
from app.handlers.dns import router as dns_router
from app.middlewares.auth import AllowedUsersMiddleware
from app.services.mikrotik import MikroTikDnsService
from app.services.ssh import SshClient


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def main() -> None:
    """Start Telegram bot polling."""

    configure_logging()
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())

    auth_middleware = AllowedUsersMiddleware(settings.allowed_users)
    dispatcher.message.middleware(auth_middleware)
    dispatcher.callback_query.middleware(auth_middleware)

    dispatcher.include_router(dns_router)
    router_catalog = RouterCatalog(settings.routers)
    dispatcher["router_catalog"] = router_catalog
    dispatcher["mikrotik_dns_services"] = {
        router.id: MikroTikDnsService(router.id, SshClient(router))
        for router in settings.routers
    }

    logging.getLogger(__name__).info("Starting Telegram bot routers=%s", len(settings.routers))
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
