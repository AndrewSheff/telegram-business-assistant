"""
API для работы с клиентами — просмотр, поиск, редактирование, история.
Все эндпоинты требуют авторизации (owner или operator).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.schemas.client import ClientListResponse, ClientResponse, ClientUpdate
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["Клиенты"])


@router.get("", response_model=ClientListResponse)
async def list_clients(
    search: str | None = Query(None, description="Поиск по имени, фамилии или username"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Список клиентов с пагинацией и поиском — для админки."""
    return await client_service.list_clients(db, search=search, page=page, size=size)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Полная инфа об одном клиенте."""
    return await client_service.get_client(client_id, db)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Обновление клиента — заметки, блокировка, телефон."""
    return await client_service.update_client(client_id, data, db)


@router.get("/{client_id}/history")
async def get_client_history(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """История клиента — последние бронирования и сообщения."""
    return await client_service.get_client_history(client_id, db)
