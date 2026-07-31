"""
Роутер бронирований — запись клиентов, статусы, фильтрация.
Все эндпоинты требуют авторизацию.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.schemas.booking import (
    BookingListResponse,
    BookingResponse,
    BookingStatusUpdate,
)
from app.services import booking_service

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.get("", response_model=BookingListResponse)
async def get_bookings(
    date_from: date | None = Query(None, description="Фильтр: дата от"),
    date_to: date | None = Query(None, description="Фильтр: дата до"),
    status: str | None = Query(None, description="Фильтр: статус бронирования"),
    client_id: uuid.UUID | None = Query(None, description="Фильтр: ID клиента"),
    service_id: uuid.UUID | None = Query(None, description="Фильтр: ID услуги"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """
    Список бронирований с фильтрацией и пагинацией.
    Можно фильтровать по дате, статусу, клиенту, услуге.
    """
    bookings, total = await booking_service.list_bookings(
        db=db,
        date_from=date_from,
        date_to=date_to,
        status=status,
        client_id=client_id,
        service_id=service_id,
        page=page,
        size=size,
    )

    # Формируем ответ с доп. полями (имя клиента, название услуги)
    items = []
    for b in bookings:
        items.append(BookingResponse(
            id=b.id,
            client_id=b.client_id,
            client_name=b.client.first_name if b.client else None,
            service_id=b.service_id,
            service_name=b.service.name if b.service else None,
            booking_date=b.booking_date,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            notes=b.notes,
            created_at=b.created_at,
        ))

    return BookingListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


# NOTE: /today идет ПЕРЕД /{booking_id} чтобы FastAPI не перехватывал
@router.get("/today", response_model=list[BookingResponse])
async def get_today_bookings(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Бронирования на сегодня — для дашборда, быстрый обзор дня."""
    bookings = await booking_service.get_today_bookings(db)

    return [
        BookingResponse(
            id=b.id,
            client_id=b.client_id,
            client_name=b.client.first_name if b.client else None,
            service_id=b.service_id,
            service_name=b.service.name if b.service else None,
            booking_date=b.booking_date,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            notes=b.notes,
            created_at=b.created_at,
        )
        for b in bookings
    ]


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Получить конкретное бронирование по id."""
    b = await booking_service.get_booking(booking_id, db)
    return BookingResponse(
        id=b.id,
        client_id=b.client_id,
        client_name=b.client.first_name if b.client else None,
        service_id=b.service_id,
        service_name=b.service.name if b.service else None,
        booking_date=b.booking_date,
        start_time=b.start_time,
        end_time=b.end_time,
        status=b.status,
        notes=b.notes,
        created_at=b.created_at,
    )


@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: uuid.UUID,
    data: BookingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """
    Обновить статус бронирования.
    Допустимые переходы:
    - pending -> confirmed / cancelled
    - confirmed -> completed / cancelled / no_show
    """
    b = await booking_service.update_booking_status(
        booking_id, data.status.value, db
    )
    return BookingResponse(
        id=b.id,
        client_id=b.client_id,
        client_name=b.client.first_name if b.client else None,
        service_id=b.service_id,
        service_name=b.service.name if b.service else None,
        booking_date=b.booking_date,
        start_time=b.start_time,
        end_time=b.end_time,
        status=b.status,
        notes=b.notes,
        created_at=b.created_at,
    )
