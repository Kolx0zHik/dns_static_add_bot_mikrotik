from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU_CALLBACK = "menu:main"
HELP_MENU_CALLBACK = "menu:help"
START_ADD_DNS_CALLBACK = "dns:add:start"
CONFIRM_ADD_DNS_CALLBACK = "dns:add:confirm"
CANCEL_ADD_DNS_CALLBACK = "dns:add:cancel"


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build main navigation keyboard."""

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
