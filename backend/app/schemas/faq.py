"""Схемы для FAQ — часто задаваемые вопросы, бот берет ответы отсюда."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class FaqResponse(BaseModel):
    """Вопрос-ответ из базы знаний FAQ."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    answer: str
    category: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime


class FaqCreate(BaseModel):
    """Создание FAQ — вопрос и ответ обязательны, категория по желанию."""

    question: str
    answer: str
    category: str | None = None
    sort_order: int | None = 0

    @field_validator("question", "answer")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Вопрос и ответ не могут быть пустыми — какой смысл тогда?"""
        if not v or not v.strip():
            raise ValueError("Поле не может быть пустым")
        return v.strip()


class FaqUpdate(BaseModel):
    """Обновление FAQ — меняем что надо, остальное не трогаем."""

    question: str | None = None
    answer: str | None = None
    category: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
