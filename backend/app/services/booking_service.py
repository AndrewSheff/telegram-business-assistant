"""
Сервис бронирований — запись клиентов на услуги.
CRUD, проверка слотов, валидация переходов статусов.
"""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.booking import Booking
from app.models.client import Client
from app.models.service import Service
from app.schemas.booking import BookingCreate

# Допустимые переходы статусов — жестко зафиксированы
VALID_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["completed", "cancelled", "no_show"],
}


async def list_bookings(
    db: AsyncSession,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    client_id: uuid.UUID | None = None,
    service_id: uuid.UUID | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Booking], int]:
    """
    Список бронирований с фильтрацией и пагинацией.
    Возвращаем кортеж (список, общее количество) — для пагинации на фронте.
    """
    # Базовый запрос
    query = select(Booking)
    count_query = select(func.count()).select_from(Booking)

    # Фильтры — сначала значение, потом null-проверка (как указано в правилах)
    if date_from is not None:
        query = query.where(Booking.booking_date >= date_from)
        count_query = count_query.where(Booking.booking_date >= date_from)

    if date_to is not None:
        query = query.where(Booking.booking_date <= date_to)
        count_query = count_query.where(Booking.booking_date <= date_to)

    if status is not None:
        query = query.where(Booking.status == status)
        count_query = count_query.where(Booking.status == status)

    if client_id is not None:
        query = query.where(Booking.client_id == client_id)
        count_query = count_query.where(Booking.client_id == client_id)

    if service_id is not None:
        query = query.where(Booking.service_id == service_id)
        count_query = count_query.where(Booking.service_id == service_id)

    # Считаем общее количество
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Пагинация и сортировка
    offset = (page - 1) * size
    query = query.order_by(
        Booking.booking_date.desc(),
        Booking.start_time.desc(),
    ).offset(offset).limit(size)

    result = await db.execute(query)
    bookings = list(result.scalars().all())

    return bookings, total


async def get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession,
) -> Booking:
    """Получаем бронирование по id — 404 если не найдено."""
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError(f"Бронирование с id {booking_id} не найдено")
    return booking


async def create_booking(
    data: BookingCreate,
    db: AsyncSession,
) -> Booking:
    """
    Создаем бронирование с проверкой доступности слота.
    Проверяем что нет пересечений с другими активными бронированиями
    на ту же дату и время.
    """
    # Проверяем что клиент существует
    client_result = await db.execute(
        select(Client).where(Client.id == data.client_id)
    )
    if client_result.scalar_one_or_none() is None:
        raise NotFoundError(f"Клиент с id {data.client_id} не найден")

    # Проверяем что услуга существует и активна
    service_result = await db.execute(
        select(Service).where(Service.id == data.service_id)
    )
    service = service_result.scalar_one_or_none()
    if service is None:
        raise NotFoundError(f"Услуга с id {data.service_id} не найдена")
    if not service.is_active:
        raise ConflictError("Эта услуга сейчас неактивна, записаться нельзя")

    # Главная проверка — нет ли пересечений по времени
    # Блокируем строки FOR UPDATE чтобы два клиента не забронировали один слот
    overlapping = await db.execute(
        select(Booking)
        .where(
            Booking.booking_date == data.booking_date,
            Booking.status.in_(["pending", "confirmed"]),
            Booking.start_time < data.end_time,
            Booking.end_time > data.start_time,
        )
        .with_for_update()
    )
    overlap_rows = overlapping.scalars().all()
    if overlap_rows:
        raise ConflictError(
            "Этот слот уже занят — выбери другое время"
        )

    booking = Booking(
        client_id=data.client_id,
        service_id=data.service_id,
        booking_date=data.booking_date,
        start_time=data.start_time,
        end_time=data.end_time,
        notes=data.notes,
        status="pending",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def update_booking_status(
    booking_id: uuid.UUID,
    status: str,
    db: AsyncSession,
) -> Booking:
    """
    Обновляем статус бронирования с проверкой допустимых переходов.
    Нельзя из completed вернуться в pending, например — только вперед.
    """
    booking = await get_booking(booking_id, db)

    current_status = booking.status
    allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])

    if status not in allowed:
        raise ConflictError(
            f"Нельзя сменить статус с '{current_status}' на '{status}'. "
            f"Допустимые переходы: {', '.join(allowed) if allowed else 'нет'}"
        )

    booking.status = status
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_today_bookings(db: AsyncSession) -> list[Booking]:
    """
    Бронирования на сегодня — удобно для дашборда.
    Сортируем по времени начала чтобы видеть хронологию.
    """
    from datetime import date as date_type
    today = date_type.today()

    result = await db.execute(
        select(Booking)
        .where(Booking.booking_date == today)
        .order_by(Booking.start_time)
    )
    return list(result.scalars().all())
