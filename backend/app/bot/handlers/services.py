"""
Хендлеры для просмотра услуг — список и детали каждой.
Клиент может посмотреть что есть и сколько стоит.
"""

import uuid

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.services import service_detail_keyboard, services_keyboard
from app.services import service_service

router = Router(name="services")
logger = structlog.get_logger(__name__)


@router.message(F.text == "Наши услуги")
async def show_services(message: Message, db):
    """Показываем список активных услуг — кнопками, красиво."""
    services = await service_service.list_services(db, include_inactive=False)

    if not services:
        await message.answer("Пока нет доступных услуг. Загляните позже!")
        return

    await message.answer(
        "Наши услуги:",
        reply_markup=services_keyboard(services),
    )


@router.callback_query(F.data.startswith("service:"))
async def show_service_detail(callback: CallbackQuery, db):
    """
    Детали конкретной услуги — название, описание, цена, длительность.
    Плюс кнопка «Записаться» если хочется.
    """
    service_id_str = callback.data.split(":")[1]

    try:
        service_id = uuid.UUID(service_id_str)
    except ValueError:
        await callback.answer("Некорректная услуга")
        return

    try:
        service = await service_service.get_service(service_id, db)
    except Exception:
        await callback.answer("Услуга не найдена")
        return

    # Формируем красивое описание
    description = service.description or "Описание отсутствует"
    text = (
        f"<b>{service.name}</b>\n\n"
        f"{description}\n\n"
        f"Цена: {service.price:.0f} р.\n"
        f"Длительность: {service.duration_minutes} мин."
    )

    await callback.message.edit_text(
        text,
        reply_markup=service_detail_keyboard(service_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, db):
    """Кнопка «Назад» — возвращаемся к списку услуг."""
    services = await service_service.list_services(db, include_inactive=False)

    if not services:
        await callback.message.edit_text("Пока нет доступных услуг.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Наши услуги:",
        reply_markup=services_keyboard(services),
    )
    await callback.answer()
