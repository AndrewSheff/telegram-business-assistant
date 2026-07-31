"""
Сервис расписания — рабочие часы, исключения, генерация слотов.
Тут самая интересная логика с вычислением свободных окошек.
"""

import uuid
from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.booking import Booking
from app.models.schedule import WorkingHours
from app.models.schedule_exception import ScheduleException
from app.models.service import Service
from app.schemas.schedule import (
    ScheduleExceptionCreate,
    TimeSlot,
    WorkingHoursUpdate,
)


async def get_working_hours(db: AsyncSession) -> list[WorkingHours]:
    """Получаем расписание на все 7 дней, сортируем по дню недели."""
    result = await db.execute(
        select(WorkingHours).order_by(WorkingHours.day_of_week)
    )
    return list(result.scalars().all())


async def update_working_hours(
    data: list[WorkingHoursUpdate],
    db: AsyncSession,
) -> list[WorkingHours]:
    """
    Обновляем рабочие часы — upsert для всех 7 дней.
    Если запись на этот день уже есть — обновляем, если нет — создаем.
    """
    result_list: list[WorkingHours] = []

    for item in data:
        # Пытаемся найти существующую запись для этого дня
        result = await db.execute(
            select(WorkingHours).where(WorkingHours.day_of_week == item.day_of_week)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем то что есть
            existing.start_time = item.start_time
            existing.end_time = item.end_time
            existing.break_start = item.break_start
            existing.break_end = item.break_end
            existing.is_working_day = item.is_working_day
            result_list.append(existing)
        else:
            # Создаем новую запись
            wh = WorkingHours(
                day_of_week=item.day_of_week,
                start_time=item.start_time,
                end_time=item.end_time,
                break_start=item.break_start,
                break_end=item.break_end,
                is_working_day=item.is_working_day,
            )
            db.add(wh)
            result_list.append(wh)

    await db.commit()

    # Рефрешим все записи чтобы получить актуальные данные
    for wh in result_list:
        await db.refresh(wh)

    return result_list


async def list_exceptions(db: AsyncSession) -> list[ScheduleException]:
    """Список исключений из расписания — отсортировано по дате."""
    result = await db.execute(
        select(ScheduleException).order_by(ScheduleException.exception_date)
    )
    return list(result.scalars().all())


async def create_exception(
    data: ScheduleExceptionCreate,
    db: AsyncSession,
) -> ScheduleException:
    """
    Создаем исключение в расписании — праздник, выходной, спецдень.
    Дублирование по дате не допускаем.
    """
    # Проверяем дубликат по дате
    existing = await db.execute(
        select(ScheduleException).where(
            ScheduleException.exception_date == data.exception_date
        )
    )
    if existing.scalar_one_or_none() is not None:
        from app.core.exceptions import ConflictError
        raise ConflictError(
            f"Исключение на дату {data.exception_date} уже существует"
        )

    exception = ScheduleException(
        exception_date=data.exception_date,
        is_working_day=data.is_working_day,
        start_time=data.start_time,
        end_time=data.end_time,
        reason=data.reason,
    )
    db.add(exception)
    await db.commit()
    await db.refresh(exception)
    return exception


async def delete_exception(
    exception_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Удаляем исключение — если нет такого, кидаем 404."""
    result = await db.execute(
        select(ScheduleException).where(ScheduleException.id == exception_id)
    )
    exception = result.scalar_one_or_none()
    if exception is None:
        raise NotFoundError(f"Исключение с id {exception_id} не найдено")

    await db.delete(exception)
    await db.commit()


def _time_to_minutes(t: time) -> int:
    """Конвертим time в минуты от начала суток — для удобства вычислений."""
    return t.hour * 60 + t.minute


def _minutes_to_time(minutes: int) -> time:
    """Обратное преобразование — из минут в time."""
    return time(hour=minutes // 60, minute=minutes % 60)


async def get_available_slots(
    target_date: date,
    service_id: uuid.UUID,
    db: AsyncSession,
) -> list[TimeSlot]:
    """
    Генерируем свободные слоты на конкретную дату для конкретной услуги.

    Алгоритм такой:
    1. Берем рабочие часы для дня недели (или исключение если есть)
    2. Генерируем все возможные слоты по длительности услуги
    3. Вычитаем перерыв
    4. Вычитаем уже занятые бронирования
    5. Профит — на выходе только свободные окошки
    """
    # Получаем услугу — нам нужна длительность
    service_result = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    service = service_result.scalar_one_or_none()
    if service is None:
        raise NotFoundError(f"Услуга с id {service_id} не найдена")

    duration = service.duration_minutes

    # Проверяем исключения — они перекрывают обычное расписание
    exception_result = await db.execute(
        select(ScheduleException).where(
            ScheduleException.exception_date == target_date
        )
    )
    exception = exception_result.scalar_one_or_none()

    if exception is not None:
        # Есть исключение — если выходной, слотов нет
        if not exception.is_working_day:
            return []
        # Рабочий день-исключение — берем его время (если не указано — слотов нет)
        if exception.start_time is None or exception.end_time is None:
            return []
        work_start = exception.start_time
        work_end = exception.end_time
        break_start = None
        break_end = None
    else:
        # Обычный день — ищем рабочие часы для этого дня недели
        day_of_week = target_date.weekday()  # 0 = пн, 6 = вс — совпадает с нашей моделью
        wh_result = await db.execute(
            select(WorkingHours).where(WorkingHours.day_of_week == day_of_week)
        )
        wh = wh_result.scalar_one_or_none()

        if wh is None or not wh.is_working_day:
            return []

        work_start = wh.start_time
        work_end = wh.end_time
        break_start = wh.break_start
        break_end = wh.break_end

    # Генерируем все возможные слоты
    start_minutes = _time_to_minutes(work_start)
    end_minutes = _time_to_minutes(work_end)

    # Перерыв в минутах (если есть)
    break_start_min = _time_to_minutes(break_start) if break_start else None
    break_end_min = _time_to_minutes(break_end) if break_end else None

    # Генерируем слоты
    all_slots: list[TimeSlot] = []
    current = start_minutes
    while current + duration <= end_minutes:
        slot_start = current
        slot_end = current + duration

        # Проверяем что слот не попадает в перерыв
        if (
            break_start_min is not None
            and break_end_min is not None
            and slot_start < break_end_min
            and slot_end > break_start_min
        ):
            # Пропускаем — перескакиваем на конец перерыва
            current = break_end_min
            continue

        all_slots.append(TimeSlot(
            start_time=_minutes_to_time(slot_start),
            end_time=_minutes_to_time(slot_end),
        ))
        current += duration

    if not all_slots:
        return []

    # Получаем существующие бронирования на эту дату (кроме отмененных и no_show)
    bookings_result = await db.execute(
        select(Booking).where(
            Booking.booking_date == target_date,
            Booking.status.in_(["pending", "confirmed"]),
        )
    )
    existing_bookings = bookings_result.scalars().all()

    # Фильтруем — убираем слоты, которые пересекаются с бронированиями
    available_slots: list[TimeSlot] = []
    for slot in all_slots:
        slot_start_min = _time_to_minutes(slot.start_time)
        slot_end_min = _time_to_minutes(slot.end_time)

        is_available = True
        for booking in existing_bookings:
            booking_start_min = _time_to_minutes(booking.start_time)
            booking_end_min = _time_to_minutes(booking.end_time)

            # Пересечение: слот начинается до конца бронирования
            # И заканчивается после начала бронирования
            if slot_start_min < booking_end_min and slot_end_min > booking_start_min:
                is_available = False
                break

        if is_available:
            available_slots.append(slot)

    return available_slots


async def init_default_schedule(db: AsyncSession) -> None:
    """
    Инициализация дефолтного расписания — пн-пт 9:00-18:00, обед 13:00-14:00.
    Суббота и воскресенье — выходные.
    Создаем только если расписания ещё нет.
    """
    # Проверяем, есть ли уже записи
    existing = await db.execute(
        select(func.count()).select_from(WorkingHours)
    )
    count = existing.scalar()
    if count and count > 0:
        return  # Расписание уже есть, не трогаем

    # Пн-Пт — рабочие дни
    for day in range(5):
        wh = WorkingHours(
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(18, 0),
            break_start=time(13, 0),
            break_end=time(14, 0),
            is_working_day=True,
        )
        db.add(wh)

    # Сб-Вс — выходные
    for day in range(5, 7):
        wh = WorkingHours(
            day_of_week=day,
            start_time=time(0, 0),
            end_time=time(0, 0),
            is_working_day=False,
        )
        db.add(wh)

    await db.commit()
