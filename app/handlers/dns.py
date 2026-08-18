from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import RouterCatalog
from app.filters.content import TextMessageFilter
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
    build_router_selection_keyboard,
    parse_select_router_callback,
    parse_start_add_dns_callback,
)
from app.models.router import RouterConfig
from app.services.exceptions import AppError, ValidationError
from app.services.mikrotik import MikroTikDnsService
from app.states.dns import AddDnsRecordStates
from app.validators.domain import normalize_and_validate_domains

logger = logging.getLogger(__name__)
router = Router(name=__name__)

MAIN_MENU_TEXT = (
    "🧭 Панель управления MikroTik DNS\n\n"
    "Выбран роутер: {router_name}\n\n"
    "Здесь можно безопасно добавить DNS Static запись "
    "типа FWD.\n"
    "Все изменения выполняются только после "
    "подтверждения.\n\n"
    "Выберите действие:"
)
ROUTER_SELECTION_TEXT = (
    "🧭 Панель управления MikroTik DNS\n\n" "Выберите MikroTik, с которым нужно работать:"
)
NO_ROUTERS_TEXT = (
    "Для вашего Telegram ID не настроен доступ ни к одному "
    "MikroTik.\n"
    "Обратитесь к администратору бота."
)
HELP_TEXT = (
    "ℹ️ Что умеет бот\n\n"
    "• принимает один или несколько доменов и проверяет их формат;\n"
    "• показывает только доступные вам MikroTik;\n"
    "• проверяет, нет ли такой записи на выбранном "
    "MikroTik;\n"
    "• добавляет DNS Static FWD запись только после "
    "подтверждения;\n"
    "• показывает понятные ошибки без технических "
    "деталей.\n\n"
    "Для начала нажмите кнопку ниже."
)
ADD_DNS_PROMPT_TEXT = (
    "➕ Добавление DNS Static FWD\n\n"
    "MikroTik: {router_name}\n\n"
    "Отправьте доменные имена одним сообщением, каждый домен с новой строки.\n\n"
    "Пример:\nexample.com\nsub.example.com"
)


def _get_user_id(message: Message | CallbackQuery) -> int | None:
    user = message.from_user
    return user.id if user else None


def _single_accessible_router(
    router_catalog: RouterCatalog,
    user_id: int | None,
) -> RouterConfig | None:
    routers = router_catalog.accessible_for_user(user_id)
    if len(routers) != 1:
        return None
    return routers[0]


def _router_from_state(
    data: dict[str, object],
    router_catalog: RouterCatalog,
    user_id: int | None,
) -> RouterConfig | None:
    router_id = data.get("router_id")
    selected_router = router_catalog.get(router_id) if isinstance(router_id, str) else None
    if selected_router is None or user_id not in selected_router.allowed_users:
        return None
    return selected_router


async def _show_router_selection_for_message(
    message: Message,
    router_catalog: RouterCatalog,
) -> None:
    routers = router_catalog.accessible_for_user(_get_user_id(message))
    if not routers:
        await message.answer(NO_ROUTERS_TEXT)
        return

    if len(routers) == 1:
        await show_main_menu(message, routers[0])
        return

    await message.answer(
        ROUTER_SELECTION_TEXT,
        reply_markup=build_router_selection_keyboard(routers),
    )


async def _show_router_selection_for_callback(
    callback: CallbackQuery,
    router_catalog: RouterCatalog,
    state: FSMContext,
) -> None:
    await state.clear()
    routers = router_catalog.accessible_for_user(_get_user_id(callback))
    if callback.message is None:
        await callback.answer()
        return
    if not routers:
        await callback.message.edit_text(NO_ROUTERS_TEXT)
        await callback.answer()
        return

    if len(routers) == 1:
        await callback.message.edit_text(
            MAIN_MENU_TEXT.format(router_name=routers[0].name),
            reply_markup=build_main_menu_keyboard(routers[0]),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        ROUTER_SELECTION_TEXT,
        reply_markup=build_router_selection_keyboard(routers),
    )
    await callback.answer()


async def show_main_menu(message: Message, router: RouterConfig) -> None:
    """Show main bot menu."""

    await message.answer(
        MAIN_MENU_TEXT.format(router_name=router.name),
        reply_markup=build_main_menu_keyboard(router),
    )


async def start_add_dns_flow(
    message: Message,
    state: FSMContext,
    router: RouterConfig,
) -> None:
    """Start DNS static record creation scenario."""

    user_id = _get_user_id(message)
    logger.info("Started add DNS flow telegram_id=%s router_id=%s", user_id, router.id)
    await state.clear()
    await state.update_data(router_id=router.id, router_name=router.name)
    await state.set_state(AddDnsRecordStates.waiting_for_domain)
    await message.answer(
        ADD_DNS_PROMPT_TEXT.format(router_name=router.name),
        reply_markup=build_domain_input_keyboard(),
    )


@router.message(Command("start"))
async def handle_start(message: Message, router_catalog: RouterCatalog) -> None:
    """Introduce available bot commands."""

    await _show_router_selection_for_message(message, router_catalog)


@router.message(Command("add"))
async def handle_add_command(
    message: Message,
    state: FSMContext,
    router_catalog: RouterCatalog,
) -> None:
    """Start DNS static record creation scenario."""

    selected_router = _single_accessible_router(router_catalog, _get_user_id(message))
    if selected_router is None:
        await _show_router_selection_for_message(message, router_catalog)
        return

    await start_add_dns_flow(message, state, selected_router)


@router.callback_query(F.data == MAIN_MENU_CALLBACK)
async def handle_main_menu_callback(
    callback: CallbackQuery,
    state: FSMContext,
    router_catalog: RouterCatalog,
) -> None:
    """Return user to the main menu."""

    await _show_router_selection_for_callback(callback, router_catalog, state)


@router.callback_query(F.data == HELP_MENU_CALLBACK)
async def handle_help_menu_callback(callback: CallbackQuery) -> None:
    """Show short user guide."""

    if callback.message is not None:
        await callback.message.edit_text(
            HELP_TEXT,
            reply_markup=build_help_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("router:select:"))
async def handle_select_router_callback(
    callback: CallbackQuery,
    state: FSMContext,
    router_catalog: RouterCatalog,
) -> None:
    """Select a MikroTik router for further actions."""

    await state.clear()
    router_id = parse_select_router_callback(callback.data or "")
    selected_router = router_catalog.get(router_id or "")
    accessible_router_ids = {
        router.id for router in router_catalog.accessible_for_user(_get_user_id(callback))
    }

    if selected_router is None or selected_router.id not in accessible_router_ids:
        await callback.answer("MikroTik недоступен.", show_alert=True)
        return

    logger.info(
        "Selected MikroTik router telegram_id=%s router_id=%s",
        _get_user_id(callback),
        selected_router.id,
    )
    if callback.message is not None:
        await callback.message.edit_text(
            MAIN_MENU_TEXT.format(router_name=selected_router.name),
            reply_markup=build_main_menu_keyboard(selected_router),
        )
    await callback.answer()


@router.callback_query(
    (F.data == START_ADD_DNS_CALLBACK) | F.data.startswith("dns:add:start:"),
)
async def handle_add_dns_callback(
    callback: CallbackQuery,
    state: FSMContext,
    router_catalog: RouterCatalog,
) -> None:
    """Start DNS static record creation from inline menu."""

    router_id = parse_start_add_dns_callback(callback.data or "")
    selected_router = (
        router_catalog.get(router_id)
        if router_id is not None
        else _single_accessible_router(router_catalog, _get_user_id(callback))
    )
    if selected_router is not None and _get_user_id(callback) not in selected_router.allowed_users:
        selected_router = None
    if selected_router is None:
        await _show_router_selection_for_callback(callback, router_catalog, state)
        return

    logger.info(
        "Started add DNS flow telegram_id=%s router_id=%s",
        _get_user_id(callback),
        selected_router.id,
    )
    await state.clear()
    await state.update_data(
        router_id=selected_router.id,
        router_name=selected_router.name,
    )
    await state.set_state(AddDnsRecordStates.waiting_for_domain)
    if callback.message is not None:
        await callback.message.edit_text(
            ADD_DNS_PROMPT_TEXT.format(router_name=selected_router.name),
            reply_markup=build_domain_input_keyboard(),
        )
    await callback.answer()


@router.message(AddDnsRecordStates.waiting_for_domain, TextMessageFilter())
async def handle_domain_input(message: Message, state: FSMContext) -> None:
    """Validate domains and ask for confirmation."""

    try:
        domains = normalize_and_validate_domains(message.text or "")
    except ValidationError as exc:
        await message.answer(
            exc.user_message,
            reply_markup=build_domain_input_keyboard(),
        )
        return

    await state.update_data(domains=domains)
    await state.set_state(AddDnsRecordStates.waiting_for_confirmation)
    data = await state.get_data()
    router_name = data.get("router_name")
    domain_list = "\n".join(domains)
    await message.answer(
        "Проверьте записи перед добавлением:\n\n"
        f"MikroTik: {router_name}\n"
        f"Домены ({len(domains)}):\n{domain_list}\n\n"
        "Тип: DNS Static FWD\n"
        "Forward to: CloudFlare\n"
        "TTL: 1d\n"
        "Address list: to-VPN",
        reply_markup=build_confirm_add_dns_keyboard(),
    )


@router.message(AddDnsRecordStates.waiting_for_domain)
async def handle_invalid_domain_message(message: Message) -> None:
    """Handle non-text, empty, or too long messages while waiting for domains."""

    if message.text is None:
        await message.answer(
            "Отправьте доменные имена текстом, каждый домен с новой строки.",
            reply_markup=build_domain_input_keyboard(),
        )
        return

    if message.text.strip() == "":
        await message.answer(
            "Введите хотя бы одно доменное имя.",
            reply_markup=build_domain_input_keyboard(),
        )
        return

    await message.answer(
        "Сообщение слишком длинное.",
        reply_markup=build_domain_input_keyboard(),
    )


@router.callback_query(
    AddDnsRecordStates.waiting_for_domain,
    F.data == CANCEL_ADD_DNS_CALLBACK,
)
async def handle_cancel_domain_input(
    callback: CallbackQuery,
    state: FSMContext,
    router_catalog: RouterCatalog,
) -> None:
    """Cancel DNS creation while waiting for a domain name."""

    data = await state.get_data()
    selected_router = _router_from_state(data, router_catalog, _get_user_id(callback))
    await state.clear()
    if callback.message is not None:
        if selected_router is None:
            await callback.message.edit_text(
                "Операция отменена. Откройте меню заново.",
            )
            await callback.answer("Операция отменена.")
            return
        await callback.message.edit_text(
            MAIN_MENU_TEXT.format(router_name=selected_router.name),
            reply_markup=build_main_menu_keyboard(selected_router),
        )
    await callback.answer("Операция отменена.")


@router.callback_query(
    AddDnsRecordStates.waiting_for_confirmation,
    F.data == CANCEL_ADD_DNS_CALLBACK,
)
async def handle_cancel_add_dns(
    callback: CallbackQuery,
    state: FSMContext,
    router_catalog: RouterCatalog,
) -> None:
    """Cancel pending DNS static record creation."""

    data = await state.get_data()
    selected_router = _router_from_state(data, router_catalog, _get_user_id(callback))
    await state.clear()
    if callback.message is not None:
        if selected_router is None:
            await callback.message.edit_text(
                "Операция отменена. Откройте меню заново.",
            )
            await callback.answer("Операция отменена.")
            return
        await callback.message.edit_text(
            MAIN_MENU_TEXT.format(router_name=selected_router.name),
            reply_markup=build_main_menu_keyboard(selected_router),
        )
    await callback.answer("Операция отменена.")


@router.callback_query(
    AddDnsRecordStates.waiting_for_confirmation,
    F.data == CONFIRM_ADD_DNS_CALLBACK,
)
async def handle_confirm_add_dns(
    callback: CallbackQuery,
    state: FSMContext,
    router_catalog: RouterCatalog,
    mikrotik_dns_services: dict[str, MikroTikDnsService],
) -> None:
    """Add DNS static FWD records after user confirmation."""

    data = await state.get_data()
    raw_domains = data.get("domains")
    router_id = data.get("router_id")
    selected_router = router_catalog.get(router_id) if isinstance(router_id, str) else None

    if (
        not isinstance(raw_domains, (list, tuple))
        or not raw_domains
        or not all(isinstance(domain, str) for domain in raw_domains)
        or selected_router is None
    ):
        await state.clear()
        await callback.answer("Заявка устарела.", show_alert=True)
        if callback.message is not None:
            await callback.message.edit_text(
                "Заявка устарела. Откройте меню заново.",
            )
        return

    domains = tuple(raw_domains)

    if _get_user_id(callback) not in selected_router.allowed_users:
        await state.clear()
        await callback.answer("MikroTik недоступен.", show_alert=True)
        if callback.message is not None:
            await callback.message.edit_text(NO_ROUTERS_TEXT)
        return

    mikrotik_dns_service = mikrotik_dns_services.get(selected_router.id)
    if mikrotik_dns_service is None:
        await state.clear()
        await callback.answer("MikroTik недоступен.", show_alert=True)
        if callback.message is not None:
            await callback.message.edit_text("MikroTik временно недоступен.")
        return

    user_id = _get_user_id(callback)
    logger.info(
        "Confirmed add DNS flow telegram_id=%s router_id=%s domains=%s",
        user_id,
        selected_router.id,
        domains,
    )

    try:
        result = await asyncio.to_thread(mikrotik_dns_service.add_fwd_records, domains)
    except AppError as exc:
        logger.exception(
            "Expected add DNS flow error telegram_id=%s router_id=%s domains=%s",
            user_id,
            selected_router.id,
            domains,
        )
        await state.clear()
        if callback.message is not None:
            await callback.message.edit_text(
                f"{exc.user_message}\n\nВыберите дальнейшее действие:",
                reply_markup=build_main_menu_keyboard(selected_router),
            )
        await callback.answer()
        return
    except Exception:
        logger.exception(
            "Unexpected add DNS flow error telegram_id=%s router_id=%s domains=%s",
            user_id,
            selected_router.id,
            domains,
        )
        await state.clear()
        if callback.message is not None:
            await callback.message.edit_text(
                "Произошла ошибка. Попробуйте позже.\n\n" "Выберите дальнейшее действие:",
                reply_markup=build_main_menu_keyboard(selected_router),
            )
        await callback.answer()
        return

    await state.clear()
    if callback.message is not None:
        result_lines = [
            "✅ Обработка списка завершена.",
            "",
            f"MikroTik: {selected_router.name}",
            f"Добавлено: {len(result.added)}",
            f"Уже существовало: {len(result.already_existed)}",
        ]
        if result.added:
            result_lines.extend(("", "Добавленные домены:", *result.added))
        if result.already_existed:
            result_lines.extend(("", "Пропущенные домены:", *result.already_existed))
        result_lines.extend(("", "Выберите дальнейшее действие:"))
        await callback.message.edit_text(
            "\n".join(result_lines),
            reply_markup=build_main_menu_keyboard(selected_router),
        )
    await callback.answer()


@router.callback_query(
    F.data.in_(
        {
            CONFIRM_ADD_DNS_CALLBACK,
            CANCEL_ADD_DNS_CALLBACK,
            MAIN_MENU_CALLBACK,
            HELP_MENU_CALLBACK,
            START_ADD_DNS_CALLBACK,
        },
    ),
)
async def handle_stale_dns_callback(callback: CallbackQuery) -> None:
    """Handle repeated clicks on old inline buttons."""

    await callback.answer("Заявка уже обработана.", show_alert=True)
