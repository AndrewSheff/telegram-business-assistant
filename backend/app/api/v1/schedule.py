"""
Роутер расписания — рабочие часы, исключения, доступные слоты.
Чтение — все авторизованные, изменение — только owner.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.schemas.schedule import (
    ScheduleExceptionCreate,
    ScheduleExceptionResponse,
    TimeSlot,
    WorkingHoursResponse,
    WorkingHoursUpdate,
)
from app.services import schedule_service

router = APIRouter(prefix="/api/v1/schedule", tags=["schedule"])


# --- Рабочие часы ---


@router.get("/hours", response_model=list[WorkingHoursResponse])
async def get_working_hours(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Получить рабочие часы на все дни недели."""
    return await schedule_service.get_working_hours(db)


@router.put("/hours", response_model=list[WorkingHoursResponse])
async def update_working_hours(
    data: list[WorkingHoursUpdate],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """
    Обновить рабочие часы — присылаем массив на все дни.
    Upsert: если день уже есть — обновим, если нет — создадим.
    """
    return await schedule_service.update_working_hours(data, db)


# --- Исключения из расписания ---


@router.get("/exceptions", response_model=list[ScheduleExceptionResponse])
async def get_exceptions(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Список всех исключений из расписания — праздники, спецдни."""
    return await schedule_service.list_exceptions(db)


@router.post(
    "/exceptions",
    response_model=ScheduleExceptionResponse,
    status_code=201,
)
async def create_exception(
    data: ScheduleExceptionCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Добавить исключение — выходной, укороченный день и т.п."""
    return await schedule_service.create_exception(data, db)


@router.delete("/exceptions/{exception_id}", status_code=204)
async def delete_exception(
    exception_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Удалить исключение из расписания."""
    await schedule_service.delete_exception(exception_id, db)


# --- Доступные слоты ---


@router.get("/slots", response_model=list[TimeSlot])
async def get_available_slots(
    date: date = Query(..., description="Дата в формате YYYY-MM-DD"),
    service_id: uuid.UUID = Query(..., description="ID услуги"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """
    Получить свободные слоты на конкретную дату для конкретной услуги.
    Учитывает рабочие часы, перерывы, исключения и существующие бронирования.
    """
    return await schedule_service.get_available_slots(date, service_id, db)
