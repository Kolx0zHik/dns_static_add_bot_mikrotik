from aiogram.types import InlineKeyboardMarkup

from app.keyboards.dns import (
    CANCEL_ADD_DNS_CALLBACK,
    CONFIRM_ADD_DNS_CALLBACK,
    HELP_MENU_CALLBACK,
    MAIN_MENU_CALLBACK,
    START_ADD_DNS_CALLBACK,
    build_confirm_add_dns_keyboard,
    build_domain_input_keyboard,
    build_help_menu_keyboard,
    build_main_menu_keyboard,
)


def _keyboard_callbacks(markup: InlineKeyboardMarkup) -> list[str]:
    return [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data is not None
    ]


def test_main_menu_keyboard_contains_primary_actions() -> None:
    assert _keyboard_callbacks(build_main_menu_keyboard()) == [
        START_ADD_DNS_CALLBACK,
        HELP_MENU_CALLBACK,
    ]


def test_help_menu_keyboard_allows_start_and_return() -> None:
    assert _keyboard_callbacks(build_help_menu_keyboard()) == [
        START_ADD_DNS_CALLBACK,
        MAIN_MENU_CALLBACK,
    ]


def test_domain_input_keyboard_allows_cancel() -> None:
    assert _keyboard_callbacks(build_domain_input_keyboard()) == [CANCEL_ADD_DNS_CALLBACK]


def test_confirm_keyboard_allows_decision_and_menu_return() -> None:
    callbacks = _keyboard_callbacks(build_confirm_add_dns_keyboard())

    assert CONFIRM_ADD_DNS_CALLBACK in callbacks
    assert CANCEL_ADD_DNS_CALLBACK in callbacks
    assert MAIN_MENU_CALLBACK in callbacks
