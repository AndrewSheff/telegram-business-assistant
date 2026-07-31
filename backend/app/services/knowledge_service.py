"""
Сервис для блоков знаний — куски контекста, которые AI подтягивает при ответах.
Владелец бизнеса заполняет, AI использует, клиенты радуются.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.knowledge_block import KnowledgeBlock
from app.schemas.knowledge import (
    KnowledgeBlockCreate,
    KnowledgeBlockResponse,
    KnowledgeBlockUpdate,
)


async def list_blocks(
    db: AsyncSession,
    active_only: bool = False,
) -> list[KnowledgeBlockResponse]:
    """
    Список блоков знаний, отсортированный по sort_order.
    active_only=True — только активные (для AI), False — все (для админки).
    """
    query = select(KnowledgeBlock)

    if active_only:
        query = query.where(KnowledgeBlock.is_active == True)  # noqa: E712

    query = query.order_by(
        KnowledgeBlock.sort_order.asc(), KnowledgeBlock.created_at.asc()
    )

    result = await db.execute(query)
    items = result.scalars().all()

    return [KnowledgeBlockResponse.model_validate(item) for item in items]


async def create_block(
    data: KnowledgeBlockCreate,
    db: AsyncSession,
) -> KnowledgeBlockResponse:
    """Создаем новый блок знаний — заголовок + контент."""
    block = KnowledgeBlock(**data.model_dump())
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return KnowledgeBlockResponse.model_validate(block)


async def update_block(
    block_id: uuid.UUID,
    data: KnowledgeBlockUpdate,
    db: AsyncSession,
) -> KnowledgeBlockResponse:
    """Обновляем блок — меняем только то, что прислали."""
    result = await db.execute(
        select(KnowledgeBlock).where(KnowledgeBlock.id == block_id)
    )
    block = result.scalar_one_or_none()

    if block is None:
        raise NotFoundError("Блок знаний не найден")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(block, field, value)

    await db.commit()
    await db.refresh(block)
    return KnowledgeBlockResponse.model_validate(block)


async def delete_block(block_id: uuid.UUID, db: AsyncSession) -> None:
    """Удаляем блок знаний — если нужно временно скрыть, лучше is_active=False."""
    result = await db.execute(
        select(KnowledgeBlock).where(KnowledgeBlock.id == block_id)
    )
    block = result.scalar_one_or_none()

    if block is None:
        raise NotFoundError("Блок знаний не найден")

    await db.delete(block)
    await db.commit()
