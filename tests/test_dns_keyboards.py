from aiogram.types import InlineKeyboardMarkup

from app.keyboards.dns import (
    CANCEL_ADD_DNS_CALLBACK,
    CONFIRM_ADD_DNS_CALLBACK,
    HELP_MENU_CALLBACK,
    MAIN_MENU_CALLBACK,
    SELECT_ROUTER_CALLBACK_PREFIX,
    START_ADD_DNS_CALLBACK,
    START_ADD_DNS_CALLBACK_PREFIX,
    build_confirm_add_dns_keyboard,
    build_domain_input_keyboard,
    build_help_menu_keyboard,
    build_main_menu_keyboard,
    build_router_info_callback,
    build_router_selection_keyboard,
)
from app.models.router import RouterConfig

ROUTER = RouterConfig(
    id="office",
    name="Office",
    host="192.0.2.1",
    port=22,
    user="admin",
    password="secret",
    allowed_users=frozenset({11111111}),
)


def _keyboard_callbacks(markup: InlineKeyboardMarkup) -> list[str]:
    return [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data is not None
    ]


def test_main_menu_keyboard_contains_primary_actions() -> None:
    assert _keyboard_callbacks(build_main_menu_keyboard(ROUTER)) == [
        build_router_info_callback(ROUTER.id),
        f"{START_ADD_DNS_CALLBACK_PREFIX}office",
        HELP_MENU_CALLBACK,
    ]


def test_router_selection_keyboard_contains_allowed_routers() -> None:
    assert _keyboard_callbacks(build_router_selection_keyboard((ROUTER,))) == [
        f"{SELECT_ROUTER_CALLBACK_PREFIX}office",
        HELP_MENU_CALLBACK,
    ]


def test_help_menu_keyboard_allows_start_and_return() -> None:
    assert _keyboard_callbacks(build_help_menu_keyboard()) == [
        START_ADD_DNS_CALLBACK,
        MAIN_MENU_CALLBACK,
    ]


def test_domain_input_keyboard_allows_cancel() -> None:
    assert _keyboard_callbacks(build_domain_input_keyboard()) == [
        CANCEL_ADD_DNS_CALLBACK,
    ]


def test_confirm_keyboard_allows_decision_and_menu_return() -> None:
    callbacks = _keyboard_callbacks(build_confirm_add_dns_keyboard())

    assert CONFIRM_ADD_DNS_CALLBACK in callbacks
    assert CANCEL_ADD_DNS_CALLBACK in callbacks
    assert MAIN_MENU_CALLBACK in callbacks


def test_parse_router_info_callback_extracts_router_id() -> None:
    from app.keyboards.dns import parse_router_info_callback

    assert parse_router_info_callback("router:info:office") == "office"
    assert parse_router_info_callback("router:info:home") == "home"
    assert parse_router_info_callback("router:info:") is None
    assert parse_router_info_callback("router:select:office") is None
    assert parse_router_info_callback("menu:main") is None
