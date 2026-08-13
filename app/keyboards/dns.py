from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CONFIRM_ADD_DNS_CALLBACK = "dns:add:confirm"
CANCEL_ADD_DNS_CALLBACK = "dns:add:cancel"


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
        ],
    )
