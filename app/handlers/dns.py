from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

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
)
from app.services.exceptions import AppError, ValidationError
from app.services.mikrotik import MikroTikDnsService
from app.states.dns import AddDnsRecordStates
from app.validators.domain import normalize_and_validate_domain

logger = logging.getLogger(__name__)
router = Router(name=__name__)

MAIN_MENU_TEXT = (
    "🧭 Панель управления MikroTik DNS\n\n"
    "Здесь можно безопасно добавить DNS Static запись "
    "типа FWD.\n"
    "Все изменения выполняются только после "
    "подтверждения.\n\n"
    "Выберите действие:"
)
HELP_TEXT = (
    "ℹ️ Что умеет бот\n\n"
    "• принимает домен и проверяет его формат;\n"
    "• проверяет, нет ли такой записи на MikroTik;\n"
    "• добавляет DNS Static FWD запись только после "
    "подтверждения;\n"
    "• показывает понятные ошибки без технических "
    "деталей.\n\n"
    "Для начала нажмите кнопку ниже."
)
ADD_DNS_PROMPT_TEXT = (
    "➕ Добавление DNS Static FWD\n\n"
    "Отправьте доменное имя одним сообщением.\n\n"
    "Пример: example.com"
)


async def show_main_menu(message: Message) -> None:
    """Show main bot menu."""

    await message.answer(MAIN_MENU_TEXT, reply_markup=build_main_menu_keyboard())


async def start_add_dns_flow(message: Message, state: FSMContext) -> None:
    """Start DNS static record creation scenario."""

    user_id = message.from_user.id if message.from_user else None
    logger.info("Started add DNS flow telegram_id=%s", user_id)
    await state.clear()
    await state.set_state(AddDnsRecordStates.waiting_for_domain)
    await message.answer(
        ADD_DNS_PROMPT_TEXT,
        reply_markup=build_domain_input_keyboard(),
    )


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Introduce available bot commands."""

    await show_main_menu(message)


@router.message(Command("add"))
async def handle_add_command(message: Message, state: FSMContext) -> None:
    """Start DNS static record creation scenario."""

    await start_add_dns_flow(message, state)


@router.callback_query(F.data == MAIN_MENU_CALLBACK)
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Return user to the main menu."""

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            MAIN_MENU_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == HELP_MENU_CALLBACK)
async def handle_help_menu_callback(callback: CallbackQuery) -> None:
    """Show short user guide."""

    if callback.message is not None:
        await callback.message.edit_text(
            HELP_TEXT,
            reply_markup=build_help_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == START_ADD_DNS_CALLBACK)
async def handle_add_dns_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Start DNS static record creation from inline menu."""

    user_id = callback.from_user.id if callback.from_user else None
    logger.info("Started add DNS flow telegram_id=%s", user_id)
    await state.clear()
    await state.set_state(AddDnsRecordStates.waiting_for_domain)
    if callback.message is not None:
        await callback.message.edit_text(
            ADD_DNS_PROMPT_TEXT,
            reply_markup=build_domain_input_keyboard(),
        )
    await callback.answer()


@router.message(AddDnsRecordStates.waiting_for_domain, TextMessageFilter())
async def handle_domain_input(message: Message, state: FSMContext) -> None:
    """Validate domain and ask for confirmation."""

    try:
        domain = normalize_and_validate_domain(message.text or "")
    except ValidationError as exc:
        await message.answer(
            exc.user_message,
            reply_markup=build_domain_input_keyboard(),
        )
        return

    await state.update_data(domain=domain)
    await state.set_state(AddDnsRecordStates.waiting_for_confirmation)
    await message.answer(
        "Проверьте запись перед добавлением:\n\n"
        f"Домен: {domain}\n"
        "Тип: DNS Static FWD\n"
        "Forward to: CloudFlare\n"
        "TTL: 1d\n"
        "Address list: to-VPN",
        reply_markup=build_confirm_add_dns_keyboard(),
    )


@router.message(AddDnsRecordStates.waiting_for_domain)
async def handle_invalid_domain_message(message: Message) -> None:
    """Handle non-text, empty, or too long messages while waiting for a domain."""

    if message.text is None:
        await message.answer(
            "Отправьте доменное имя текстом.",
            reply_markup=build_domain_input_keyboard(),
        )
        return

    if message.text.strip() == "":
        await message.answer(
            "Введите доменное имя.",
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
) -> None:
    """Cancel DNS creation while waiting for a domain name."""

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            MAIN_MENU_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer("Операция отменена.")


@router.callback_query(
    AddDnsRecordStates.waiting_for_confirmation,
    F.data == CANCEL_ADD_DNS_CALLBACK,
)
async def handle_cancel_add_dns(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel pending DNS static record creation."""

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            MAIN_MENU_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer("Операция отменена.")


@router.callback_query(
    AddDnsRecordStates.waiting_for_confirmation,
    F.data == CONFIRM_ADD_DNS_CALLBACK,
)
async def handle_confirm_add_dns(
    callback: CallbackQuery,
    state: FSMContext,
    mikrotik_dns_service: MikroTikDnsService,
) -> None:
    """Add DNS static FWD record after user confirmation."""

    data = await state.get_data()
    domain = data.get("domain")

    if not isinstance(domain, str):
        await state.clear()
        await callback.answer("Заявка устарела.", show_alert=True)
        if callback.message is not None:
            await callback.message.edit_text(
                MAIN_MENU_TEXT,
                reply_markup=build_main_menu_keyboard(),
            )
        return

    user_id = callback.from_user.id if callback.from_user else None
    logger.info("Confirmed add DNS flow telegram_id=%s domain=%s", user_id, domain)

    try:
        await asyncio.to_thread(mikrotik_dns_service.add_fwd_record, domain)
    except AppError as exc:
        logger.exception(
            "Expected add DNS flow error telegram_id=%s domain=%s",
            user_id,
            domain,
        )
        await state.clear()
        if callback.message is not None:
            await callback.message.edit_text(
                f"{exc.user_message}\n\nВыберите дальнейшее действие:",
                reply_markup=build_main_menu_keyboard(),
            )
        await callback.answer()
        return
    except Exception:
        logger.exception(
            "Unexpected add DNS flow error telegram_id=%s domain=%s",
            user_id,
            domain,
        )
        await state.clear()
        if callback.message is not None:
            await callback.message.edit_text(
                "Произошла ошибка. Попробуйте позже.\n\n"
                "Выберите дальнейшее действие:",
                reply_markup=build_main_menu_keyboard(),
            )
        await callback.answer()
        return

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            f"✅ Запись успешно добавлена.\n\n"
            f"Домен: {domain}\n\n"
            "Выберите дальнейшее действие:",
            reply_markup=build_main_menu_keyboard(),
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
