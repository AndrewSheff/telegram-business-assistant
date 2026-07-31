"""
Хендлеры для процесса записи на услугу — FSM-машинка.
Шаги: выбор услуги -> дата -> время -> подтверждение.
Можно отменить на любом этапе через /cancel.
"""

import uuid
from datetime import date, datetime, timedelta

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.calendar import calendar_keyboard
from app.bot.keyboards.common import confirm_booking_keyboard, time_slots_keyboard
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.services import services_keyboard
from app.bot.states.booking import BookingStates
from app.core.exceptions import ConflictError
from app.models.client import Client
from app.schemas.booking import BookingCreate
from app.services import booking_service, schedule_service, service_service

router = Router(name="booking")
logger = structlog.get_logger(__name__)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Команда /cancel — выход из FSM на любом шаге."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять, ты и так в меню.")
        return

    await state.clear()
    await message.answer(
        "Запись отменена. Возвращаемся в меню.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "Записаться")
async def start_booking_text(message: Message, state: FSMContext, db):
    """Кнопка «Записаться» из главного меню — показываем список услуг."""
    services = await service_service.list_services(db, include_inactive=False)

    if not services:
        await message.answer("Сейчас нет доступных услуг для записи.")
        return

    await state.set_state(BookingStates.choosing_service)
    await message.answer(
        "Выбери услугу для записи:",
        reply_markup=services_keyboard(services),
    )


@router.callback_query(F.data.startswith("book:"))
async def start_booking_callback(callback: CallbackQuery, state: FSMContext, db):
    """
    Кнопка «Записаться» из карточки услуги — сразу переходим к выбору даты.
    Услуга уже выбрана, не нужно снова показывать список.
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

    # Сохраняем выбранную услугу в FSM
    await state.update_data(
        service_id=str(service.id),
        service_name=service.name,
        service_price=float(service.price),
        service_duration=service.duration_minutes,
    )

    # Переходим к выбору даты
    await _show_calendar(callback.message, state, service.id, db, edit=True)
    await callback.answer()


@router.callback_query(BookingStates.choosing_service, F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext, db):
    """Выбрали услугу из списка — сохраняем и идем к календарю."""
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

    await state.update_data(
        service_id=str(service.id),
        service_name=service.name,
        service_price=float(service.price),
        service_duration=service.duration_minutes,
    )

    await _show_calendar(callback.message, state, service.id, db, edit=True)
    await callback.answer()


async def _show_calendar(
    message: Message,
    state: FSMContext,
    service_id: uuid.UUID,
    db,
    edit: bool = False,
):
    """
    Показываем календарь с доступными датами.
    Проверяем следующие 14 дней — если есть хоть один свободный слот, день доступен.
    """
    today = date.today()
    available_dates: list[date] = []

    # Проверяем 14 дней вперед
    for day_offset in range(1, 15):
        check_date = today + timedelta(days=day_offset)
        slots = await schedule_service.get_available_slots(check_date, service_id, db)
        if slots:
            available_dates.append(check_date)

    await state.set_state(BookingStates.choosing_date)

    text = "Выбери удобную дату:"

    if not available_dates:
        text = "К сожалению, в ближайшие 14 дней нет свободных дат."

    if edit:
        await message.edit_text(text, reply_markup=calendar_keyboard(available_dates))
    else:
        await message.answer(text, reply_markup=calendar_keyboard(available_dates))


@router.callback_query(BookingStates.choosing_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, db):
    """Выбрали дату — показываем свободные временные слоты."""
    date_str = callback.data.split(":")[1]

    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        await callback.answer("Некорректная дата")
        return

    data = await state.get_data()
    service_id = uuid.UUID(data["service_id"])

    # Получаем свободные слоты на эту дату
    slots = await schedule_service.get_available_slots(selected_date, service_id, db)

    if not slots:
        await callback.answer("На эту дату нет свободных слотов, выбери другую")
        return

    await state.update_data(selected_date=date_str)
    await state.set_state(BookingStates.choosing_time)

    await callback.message.edit_text(
        f"Свободные слоты на {selected_date.strftime('%d.%m.%Y')}:",
        reply_markup=time_slots_keyboard(slots),
    )
    await callback.answer()


@router.callback_query(BookingStates.choosing_time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    """Выбрали время — показываем сводку для подтверждения."""
    time_str = callback.data.split(":", 1)[1]

    try:
        selected_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await callback.answer("Некорректное время")
        return

    data = await state.get_data()
    service_name = data["service_name"]
    service_price = data["service_price"]
    service_duration = data["service_duration"]
    selected_date = date.fromisoformat(data["selected_date"])

    # Вычисляем время окончания
    start_dt = datetime.combine(selected_date, selected_time)
    end_dt = start_dt + timedelta(minutes=service_duration)
    end_time = end_dt.time()

    await state.update_data(
        selected_time=time_str,
        end_time=end_time.strftime("%H:%M"),
    )
    await state.set_state(BookingStates.confirming)

    # Сводка для подтверждения
    summary = (
        f"<b>Подтверди запись:</b>\n\n"
        f"Услуга: {service_name}\n"
        f"Дата: {selected_date.strftime('%d.%m.%Y')}\n"
        f"Время: {selected_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
        f"Стоимость: {service_price:.0f} р."
    )

    await callback.message.edit_text(
        summary,
        reply_markup=confirm_booking_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(BookingStates.confirming, F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, db, client: Client):
    """
    Подтверждение записи — создаем бронирование через сервис.
    Если слот уже заняли — сообщаем и предлагаем выбрать другой.
    """
    data = await state.get_data()

    service_id = uuid.UUID(data["service_id"])
    selected_date = date.fromisoformat(data["selected_date"])
    selected_time = datetime.strptime(data["selected_time"], "%H:%M").time()
    end_time = datetime.strptime(data["end_time"], "%H:%M").time()

    booking_data = BookingCreate(
        client_id=client.id,
        service_id=service_id,
        booking_date=selected_date,
        start_time=selected_time,
        end_time=end_time,
    )

    try:
        await booking_service.create_booking(booking_data, db)
    except ConflictError as e:
        logger.warning("booking_slot_conflict", error=str(e))
        await callback.message.edit_text(
            "Этот слот уже занят. Попробуй выбрать другое время."
        )
    except Exception as e:
        logger.error("booking_creation_failed", error=str(e))
        await callback.message.edit_text(
            "Не удалось создать запись. Попробуй позже."
        )
        await state.clear()
        await callback.answer()
        return

    await state.clear()

    service_name = data["service_name"]
    success_text = (
        f"Запись создана!\n\n"
        f"Услуга: {service_name}\n"
        f"Дата: {selected_date.strftime('%d.%m.%Y')}\n"
        f"Время: {selected_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n\n"
        f"Ждем тебя!"
    )

    await callback.message.edit_text(success_text)
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()

    logger.info(
        "booking_created_via_bot",
        client_id=str(client.id),
        service_id=str(service_id),
        date=str(selected_date),
    )


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_flow(callback: CallbackQuery, state: FSMContext):
    """Отмена записи на любом шаге FSM — чистим состояние и в меню."""
    await state.clear()
    await callback.message.edit_text("Запись отменена.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Пустышки в календаре — просто игнорим клик."""
    await callback.answer()
