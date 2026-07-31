"""
Хендлеры для раздела «Мои записи» — клиент смотрит свои записи и может отменить.
Показываем только активные (pending/confirmed), прошедшие не интересны.
"""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models.client import Client
from app.services import booking_service, settings_service

router = Router(name="my_bookings")
logger = structlog.get_logger(__name__)


@router.message(F.text == "Мои записи")
async def show_my_bookings(message: Message, db, client: Client):
    """Показываем список активных записей клиента с кнопками отмены."""
    # Сначала pending
    pending_bookings, _ = await booking_service.list_bookings(
        db=db,
        client_id=client.id,
        status="pending",
        page=1,
        size=50,
    )
    # Потом confirmed
    confirmed_bookings, _ = await booking_service.list_bookings(
        db=db,
        client_id=client.id,
        status="confirmed",
        page=1,
        size=50,
    )
    active_bookings = pending_bookings + confirmed_bookings

    if not active_bookings:
        await message.answer(
            "У тебя пока нет активных записей.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = "<b>Твои записи:</b>\n\n"
    buttons = []

    for booking in active_bookings:
        # Название услуги — берем из связи
        service_name = booking.service.name if booking.service else "Услуга"

        status_emoji = "⏳" if booking.status == "pending" else "✅"
        status_text = "Ожидает подтверждения" if booking.status == "pending" else "Подтверждена"

        text += (
            f"{status_emoji} <b>{service_name}</b>\n"
            f"   Дата: {booking.booking_date.strftime('%d.%m.%Y')}\n"
            f"   Время: {booking.start_time.strftime('%H:%M')} - "
            f"{booking.end_time.strftime('%H:%M')}\n"
            f"   Статус: {status_text}\n\n"
        )

        buttons.append([
            InlineKeyboardButton(
                text=f"Отменить: {service_name} ({booking.booking_date.strftime('%d.%m')})",
                callback_data=f"cancel_my:{booking.id}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("cancel_my:"))
async def confirm_cancel_booking(callback: CallbackQuery, db, client: Client):
    """
    Клиент нажал «Отменить» — проверяем можно ли отменить (min_cancel_hours).
    Если можно — спрашиваем подтверждение.
    """
    booking_id_str = callback.data.split(":")[1]

    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await callback.answer("Некорректная запись")
        return

    try:
        booking = await booking_service.get_booking(booking_id, db)
    except Exception:
        await callback.answer("Запись не найдена")
        return

    # Проверяем что это запись именно этого клиента
    if booking.client_id != client.id:
        await callback.answer("Это не твоя запись")
        return

    # Проверяем min_cancel_hours
    settings = await settings_service.get_settings(db)
    min_hours = settings.min_cancel_hours or 24

    booking_datetime = datetime.combine(booking.booking_date, booking.start_time)
    # Делаем naive datetime для сравнения
    now = datetime.now(UTC).replace(tzinfo=None)
    time_left = booking_datetime - now

    if time_left < timedelta(hours=min_hours):
        await callback.answer(
            f"Отменить можно не позднее чем за {min_hours} ч. до записи",
            show_alert=True,
        )
        return

    # Спрашиваем подтверждение
    service_name = booking.service.name if booking.service else "Услуга"
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, отменить",
                    callback_data=f"confirm_cancel:{booking_id}",
                ),
                InlineKeyboardButton(
                    text="Нет, оставить",
                    callback_data="keep_booking",
                ),
            ],
        ]
    )

    await callback.message.edit_text(
        f"Точно отменить запись на <b>{service_name}</b> "
        f"{booking.booking_date.strftime('%d.%m.%Y')} "
        f"в {booking.start_time.strftime('%H:%M')}?",
        reply_markup=confirm_keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_cancel:"))
async def do_cancel_booking(callback: CallbackQuery, db, client: Client):
    """Подтверждение отмены — меняем статус на cancelled."""
    booking_id_str = callback.data.split(":")[1]

    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await callback.answer("Некорректная запись")
        return

    try:
        booking = await booking_service.get_booking(booking_id, db)
    except Exception:
        await callback.answer("Запись не найдена")
        return

    if booking.client_id != client.id:
        await callback.answer("Это не твоя запись")
        return

    try:
        await booking_service.update_booking_status(booking_id, "cancelled", db)
    except Exception as e:
        logger.error("booking_cancel_failed", booking_id=str(booking_id), error=str(e))
        await callback.message.edit_text("Не удалось отменить запись. Попробуй позже.")
        await callback.answer()
        return

    await callback.message.edit_text("Запись успешно отменена.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()

    logger.info("booking_cancelled_by_client", booking_id=str(booking_id))


@router.callback_query(F.data == "keep_booking")
async def keep_booking(callback: CallbackQuery):
    """Клиент передумал отменять — ок, оставляем."""
    await callback.message.edit_text("Хорошо, запись сохранена.")
    await callback.answer()
