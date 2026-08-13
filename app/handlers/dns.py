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
    build_confirm_add_dns_keyboard,
)
from app.services.exceptions import AppError, ValidationError
from app.services.mikrotik import MikroTikDnsService
from app.states.dns import AddDnsRecordStates
from app.validators.domain import normalize_and_validate_domain

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Introduce available bot commands."""

    await message.answer("Бот готов. Используйте /add для добавления DNS Static FWD записи.")


@router.message(Command("add"))
async def handle_add_command(message: Message, state: FSMContext) -> None:
    """Start DNS static record creation scenario."""

    user_id = message.from_user.id if message.from_user else None
    logger.info("Started add DNS flow telegram_id=%s", user_id)
    await state.clear()
    await state.set_state(AddDnsRecordStates.waiting_for_domain)
    await message.answer("Введите доменное имя.")


@router.message(AddDnsRecordStates.waiting_for_domain, TextMessageFilter())
async def handle_domain_input(message: Message, state: FSMContext) -> None:
    """Validate domain and ask for confirmation."""

    try:
        domain = normalize_and_validate_domain(message.text or "")
    except ValidationError as exc:
        await message.answer(exc.user_message)
        return

    await state.update_data(domain=domain)
    await state.set_state(AddDnsRecordStates.waiting_for_confirmation)
    await message.answer(
        f"Добавить запись?\n\n{domain}",
        reply_markup=build_confirm_add_dns_keyboard(),
    )


@router.message(AddDnsRecordStates.waiting_for_domain)
async def handle_invalid_domain_message(message: Message) -> None:
    """Handle non-text, empty, or too long messages while waiting for a domain."""

    if message.text is None:
        await message.answer("Отправьте доменное имя текстом.")
        return

    if message.text.strip() == "":
        await message.answer("Введите доменное имя.")
        return

    await message.answer("Сообщение слишком длинное.")


@router.callback_query(
    AddDnsRecordStates.waiting_for_confirmation,
    F.data == CANCEL_ADD_DNS_CALLBACK,
)
async def handle_cancel_add_dns(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel pending DNS static record creation."""

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text("Операция отменена.")
    await callback.answer()


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
            await callback.message.edit_text("Заявка устарела. Используйте /add заново.")
        return

    user_id = callback.from_user.id if callback.from_user else None
    logger.info("Confirmed add DNS flow telegram_id=%s domain=%s", user_id, domain)

    try:
        await asyncio.to_thread(mikrotik_dns_service.add_fwd_record, domain)
    except AppError as exc:
        logger.exception("Expected add DNS flow error telegram_id=%s domain=%s", user_id, domain)
        await state.clear()
        if callback.message is not None:
            await callback.message.edit_text(exc.user_message)
        await callback.answer()
        return
    except Exception:
        logger.exception("Unexpected add DNS flow error telegram_id=%s domain=%s", user_id, domain)
        await state.clear()
        if callback.message is not None:
            await callback.message.edit_text("Произошла ошибка. Попробуйте позже.")
        await callback.answer()
        return

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text("Запись успешно добавлена.")
    await callback.answer()


@router.callback_query(F.data.in_({CONFIRM_ADD_DNS_CALLBACK, CANCEL_ADD_DNS_CALLBACK}))
async def handle_stale_dns_callback(callback: CallbackQuery) -> None:
    """Handle repeated clicks on old inline buttons."""

    await callback.answer("Заявка уже обработана.", show_alert=True)
