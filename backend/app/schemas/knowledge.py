"""Схемы для блоков знаний — дополнительная инфа для AI-ассистента."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeBlockResponse(BaseModel):
    """Блок знаний — кусочек контекста, который AI использует при ответах."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    is_active: bool
    sort_order: int
    created_at: datetime


class KnowledgeBlockCreate(BaseModel):
    """Создание блока знаний — заголовок и содержимое, порядок опционально."""

    title: str
    content: str
    sort_order: int | None = 0


class KnowledgeBlockUpdate(BaseModel):
    """Обновление блока знаний — любое поле по отдельности."""

    title: str | None = None
    content: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
