"""
API для FAQ — просмотр для всех авторизованных, создание/изменение/удаление только owner.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.schemas.faq import FaqCreate, FaqResponse, FaqUpdate
from app.services import faq_service

router = APIRouter(prefix="/faq", tags=["FAQ"])


@router.get("", response_model=list[FaqResponse])
async def list_faq(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Все FAQ — для админки показываем и активные, и скрытые."""
    return await faq_service.list_faq(db, active_only=False)


@router.post("", response_model=FaqResponse, status_code=201)
async def create_faq(
    data: FaqCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Создать новый FAQ — только для владельца."""
    return await faq_service.create_faq(data, db)


@router.put("/{faq_id}", response_model=FaqResponse)
async def update_faq(
    faq_id: uuid.UUID,
    data: FaqUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Обновить FAQ — только для владельца."""
    return await faq_service.update_faq(faq_id, data, db)


@router.delete("/{faq_id}", status_code=204)
async def delete_faq(
    faq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Удалить FAQ — только для владельца, действие необратимо."""
    await faq_service.delete_faq(faq_id, db)
