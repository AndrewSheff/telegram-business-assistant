"""
API для рассылок — полный CRUD + запуск отправки.
Все эндпоинты только для owner — рассылки дело серьезное.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.database import get_db
from app.schemas.broadcast import BroadcastCreate, BroadcastListResponse, BroadcastResponse
from app.services import broadcast_service

router = APIRouter(prefix="/broadcasts", tags=["Рассылки"])


@router.get("", response_model=BroadcastListResponse)
async def list_broadcasts(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Список рассылок с пагинацией — новые первые."""
    return await broadcast_service.list_broadcasts(db, page=page, size=size)


@router.post("", response_model=BroadcastResponse, status_code=201)
async def create_broadcast(
    data: BroadcastCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("owner")),
):
    """Создать новую рассылку — будет в статусе 'draft'."""
    return await broadcast_service.create_broadcast(data, current_user.id, db)


@router.get("/{broadcast_id}")
async def get_broadcast(
    broadcast_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Детали рассылки + статистика по логам отправки."""
    return await broadcast_service.get_broadcast(broadcast_id, db)


@router.post("/{broadcast_id}/send", response_model=BroadcastResponse)
async def send_broadcast(
    broadcast_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Запустить отправку рассылки — создает логи для всех получателей."""
    return await broadcast_service.start_send(broadcast_id, db)


@router.delete("/{broadcast_id}", status_code=204)
async def delete_broadcast(
    broadcast_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Удалить рассылку — можно только черновик."""
    await broadcast_service.delete_broadcast(broadcast_id, db)
