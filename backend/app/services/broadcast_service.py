"""
Сервис для рассылок — создание, отправка, сегментация.
Фактическую отправку в Telegram делает отдельная задача,
тут только подготовка: создание логов для каждого получателя.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.booking import Booking
from app.models.broadcast import Broadcast
from app.models.broadcast_log import BroadcastLog
from app.models.client import Client
from app.schemas.broadcast import BroadcastCreate, BroadcastListResponse, BroadcastResponse


async def list_broadcasts(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
) -> BroadcastListResponse:
    """Список рассылок с пагинацией — новые первые."""
    # считаем общее количество
    count_result = await db.execute(select(func.count()).select_from(Broadcast))
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    query = (
        select(Broadcast)
        .order_by(Broadcast.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return BroadcastListResponse(
        items=[BroadcastResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        size=size,
    )


async def create_broadcast(
    data: BroadcastCreate,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> BroadcastResponse:
    """Создаем рассылку — сначала как черновик, отправка отдельно."""
    broadcast = Broadcast(
        **data.model_dump(),
        created_by=user_id,
        status="draft",
    )
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    return BroadcastResponse.model_validate(broadcast)


async def get_broadcast(
    broadcast_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Получаем рассылку + считаем кол-во логов по статусам.
    Удобно для детального просмотра в админке.
    """
    result = await db.execute(
        select(Broadcast).where(Broadcast.id == broadcast_id)
    )
    broadcast = result.scalar_one_or_none()

    if broadcast is None:
        raise NotFoundError("Рассылка не найдена")

    # считаем логи по статусам
    logs_count_query = (
        select(
            BroadcastLog.status,
            func.count(BroadcastLog.id).label("count"),
        )
        .where(BroadcastLog.broadcast_id == broadcast_id)
        .group_by(BroadcastLog.status)
    )
    logs_result = await db.execute(logs_count_query)
    logs_stats = {row.status: row.count for row in logs_result.all()}

    broadcast_data = BroadcastResponse.model_validate(broadcast)

    return {
        "broadcast": broadcast_data,
        "logs_stats": logs_stats,
    }


async def delete_broadcast(
    broadcast_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Удаляем рассылку — только если она ещё черновик, отправленную не трогаем."""
    result = await db.execute(
        select(Broadcast).where(Broadcast.id == broadcast_id)
    )
    broadcast = result.scalar_one_or_none()

    if broadcast is None:
        raise NotFoundError("Рассылка не найдена")

    if broadcast.status != "draft":
        raise AppError(
            status_code=400,
            detail="Удалить можно только черновик рассылки",
        )

    await db.delete(broadcast)
    await db.commit()


async def start_send(
    broadcast_id: uuid.UUID,
    db: AsyncSession,
) -> BroadcastResponse:
    """
    Запускаем отправку рассылки:
    1. Проверяем что она в статусе draft
    2. Выбираем целевых клиентов по сегменту
    3. Создаем broadcast_log для каждого получателя
    4. Ставим статус 'sending'

    Фактическая отправка в Telegram будет в фоновой задаче.
    """
    result = await db.execute(
        select(Broadcast).where(Broadcast.id == broadcast_id)
    )
    broadcast = result.scalar_one_or_none()

    if broadcast is None:
        raise NotFoundError("Рассылка не найдена")

    if broadcast.status != "draft":
        raise AppError(
            status_code=400,
            detail="Отправить можно только черновик рассылки",
        )

    # Проверяем что бот настроен — без него рассылка бессмысленна
    from app.config import settings as app_settings
    if not app_settings.TELEGRAM_BOT_TOKEN:
        raise AppError(
            status_code=400,
            detail="Telegram-бот не настроен. Задайте токен бота в настройках.",
        )

    # выбираем клиентов по сегменту
    clients_query = select(Client).where(Client.is_blocked == False)  # noqa: E712

    if broadcast.segment == "recent":
        # клиенты с бронированиями за последние N дней
        days = broadcast.segment_days or 30
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).date()
        recent_clients_sq = (
            select(Booking.client_id)
            .where(Booking.booking_date >= cutoff_date)
            .distinct()
            .scalar_subquery()
        )
        clients_query = clients_query.where(Client.id.in_(recent_clients_sq))

    elif broadcast.segment == "inactive":
        # клиенты без бронирований за последние N дней (или вообще без бронирований)
        days = broadcast.segment_days or 30
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).date()
        active_clients_sq = (
            select(Booking.client_id)
            .where(Booking.booking_date >= cutoff_date)
            .distinct()
            .scalar_subquery()
        )
        clients_query = clients_query.where(Client.id.notin_(active_clients_sq))

    # сегмент 'all' — все не заблокированные, фильтр уже есть

    clients_result = await db.execute(clients_query)
    target_clients = clients_result.scalars().all()

    # создаем логи для каждого получателя
    for client in target_clients:
        log = BroadcastLog(
            broadcast_id=broadcast.id,
            client_id=client.id,
            status="pending",
        )
        db.add(log)

    # обновляем рассылку
    broadcast.status = "sending"
    broadcast.total_count = len(target_clients)

    await db.commit()
    await db.refresh(broadcast)

    return BroadcastResponse.model_validate(broadcast)
