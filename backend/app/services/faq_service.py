"""
Сервис для FAQ — CRUD для часто задаваемых вопросов.
Бот дергает их перед тем как лезть в AI, чтобы не тратить токены зря.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.faq import FaqItem
from app.schemas.faq import FaqCreate, FaqResponse, FaqUpdate


async def list_faq(
    db: AsyncSession,
    active_only: bool = False,
) -> list[FaqResponse]:
    """
    Список FAQ, отсортированный по sort_order.
    active_only=True — только активные (для бота), False — все (для админки).
    """
    query = select(FaqItem)

    if active_only:
        query = query.where(FaqItem.is_active == True)  # noqa: E712

    query = query.order_by(FaqItem.sort_order.asc(), FaqItem.created_at.asc())

    result = await db.execute(query)
    items = result.scalars().all()

    return [FaqResponse.model_validate(item) for item in items]


async def get_faq(faq_id: uuid.UUID, db: AsyncSession) -> FaqResponse:
    """Получаем один FAQ по id — 404 если не нашли."""
    result = await db.execute(select(FaqItem).where(FaqItem.id == faq_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise NotFoundError("FAQ не найден")

    return FaqResponse.model_validate(item)


async def create_faq(data: FaqCreate, db: AsyncSession) -> FaqResponse:
    """Создаем новый FAQ — вопрос и ответ обязательны."""
    item = FaqItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return FaqResponse.model_validate(item)


async def update_faq(
    faq_id: uuid.UUID,
    data: FaqUpdate,
    db: AsyncSession,
) -> FaqResponse:
    """Обновляем FAQ — меняем только те поля, что реально пришли."""
    result = await db.execute(select(FaqItem).where(FaqItem.id == faq_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise NotFoundError("FAQ не найден")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return FaqResponse.model_validate(item)


async def delete_faq(faq_id: uuid.UUID, db: AsyncSession) -> None:
    """Удаляем FAQ — безвозвратно, если нужно скрыть — ставь is_active=False."""
    result = await db.execute(select(FaqItem).where(FaqItem.id == faq_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise NotFoundError("FAQ не найден")

    await db.delete(item)
    await db.commit()
