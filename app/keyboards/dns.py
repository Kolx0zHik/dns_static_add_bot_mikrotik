from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.router import RouterConfig

MAIN_MENU_CALLBACK = "menu:main"
HELP_MENU_CALLBACK = "menu:help"
START_ADD_DNS_CALLBACK = "dns:add:start"
START_ADD_DNS_CALLBACK_PREFIX = "dns:add:start:"
CONFIRM_ADD_DNS_CALLBACK = "dns:add:confirm"
CANCEL_ADD_DNS_CALLBACK = "dns:add:cancel"
SELECT_ROUTER_CALLBACK_PREFIX = "router:select:"
ROUTER_INFO_CALLBACK_PREFIX = "router:info:"


def build_select_router_callback(router_id: str) -> str:
    """Build callback data for router selection."""

    return f"{SELECT_ROUTER_CALLBACK_PREFIX}{router_id}"


def build_router_info_callback(router_id: str) -> str:
    """Build callback data for router info."""

    return f"{ROUTER_INFO_CALLBACK_PREFIX}{router_id}"


def build_start_add_dns_callback(router_id: str) -> str:
    """Build callback data for starting DNS record creation on a router."""

    return f"{START_ADD_DNS_CALLBACK_PREFIX}{router_id}"


def parse_start_add_dns_callback(callback_data: str) -> str | None:
    """Parse router ID from add DNS callback."""

    if callback_data == START_ADD_DNS_CALLBACK:
        return None
    if not callback_data.startswith(START_ADD_DNS_CALLBACK_PREFIX):
        return None
    router_id = callback_data.removeprefix(START_ADD_DNS_CALLBACK_PREFIX)
    return router_id or None


def parse_select_router_callback(callback_data: str) -> str | None:
    """Parse router ID from router selection callback."""

    if not callback_data.startswith(SELECT_ROUTER_CALLBACK_PREFIX):
        return None
    router_id = callback_data.removeprefix(SELECT_ROUTER_CALLBACK_PREFIX)
    return router_id or None


def parse_router_info_callback(callback_data: str) -> str | None:
    """Parse router ID from router info callback."""

    if not callback_data.startswith(ROUTER_INFO_CALLBACK_PREFIX):
        return None
    router_id = callback_data.removeprefix(ROUTER_INFO_CALLBACK_PREFIX)
    return router_id or None


def build_router_selection_keyboard(routers: tuple[RouterConfig, ...]) -> InlineKeyboardMarkup:
    """Build keyboard with routers available for a user."""

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"📍 {router.name}",
                callback_data=build_select_router_callback(router.id),
            ),
        ]
        for router in routers
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text="ℹ️ Что умеет бот",
                callback_data=HELP_MENU_CALLBACK,
            ),
        ],
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_main_menu_keyboard(router: RouterConfig) -> InlineKeyboardMarkup:
    """Build main navigation keyboard."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📍 {router.name}",
                    callback_data=build_router_info_callback(router.id),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ Добавить DNS FWD",
                    callback_data=build_start_add_dns_callback(router.id),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Что умеет бот",
                    callback_data=HELP_MENU_CALLBACK,
                ),
            ],
        ],
    )


def build_help_menu_keyboard() -> InlineKeyboardMarkup:
    """Build help screen keyboard."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить DNS FWD",
                    callback_data=START_ADD_DNS_CALLBACK,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data=MAIN_MENU_CALLBACK,
                ),
            ],
        ],
    )


def build_domain_input_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard shown while waiting for a domain name."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=CANCEL_ADD_DNS_CALLBACK,
                ),
            ],
        ],
    )


def build_confirm_add_dns_keyboard() -> InlineKeyboardMarkup:
    """Build confirmation keyboard for DNS record creation."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Добавить",
                    callback_data=CONFIRM_ADD_DNS_CALLBACK,
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=CANCEL_ADD_DNS_CALLBACK,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data=MAIN_MENU_CALLBACK,
                ),
            ],
        ],
    )
