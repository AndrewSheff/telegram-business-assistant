"""
API для блоков знаний — все эндпоинты только для owner.
Это конфиденциальная инфа бизнеса, операторам не показываем.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.database import get_db
from app.schemas.knowledge import (
    KnowledgeBlockCreate,
    KnowledgeBlockResponse,
    KnowledgeBlockUpdate,
)
from app.services import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["База знаний"])


@router.get("", response_model=list[KnowledgeBlockResponse])
async def list_blocks(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Все блоки знаний — и активные, и скрытые."""
    return await knowledge_service.list_blocks(db, active_only=False)


@router.post("", response_model=KnowledgeBlockResponse, status_code=201)
async def create_block(
    data: KnowledgeBlockCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Создать новый блок знаний."""
    return await knowledge_service.create_block(data, db)


@router.put("/{block_id}", response_model=KnowledgeBlockResponse)
async def update_block(
    block_id: uuid.UUID,
    data: KnowledgeBlockUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Обновить блок знаний."""
    return await knowledge_service.update_block(block_id, data, db)


@router.delete("/{block_id}", status_code=204)
async def delete_block(
    block_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Удалить блок знаний — необратимо, лучше сначала подумать."""
    await knowledge_service.delete_block(block_id, db)
