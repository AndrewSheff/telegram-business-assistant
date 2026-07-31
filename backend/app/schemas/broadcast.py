"""Схемы для рассылок — массовые сообщения клиентам через бота."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class BroadcastSegment(str, Enum):
    """Сегменты для рассылки — кому шлем."""

    all = "all"
    recent = "recent"
    inactive = "inactive"


class BroadcastStatus(str, Enum):
    """Статус рассылки — от черновика до завершения."""

    draft = "draft"
    scheduled = "scheduled"
    sending = "sending"
    completed = "completed"
    failed = "failed"


class BroadcastResponse(BaseModel):
    """Полная инфа о рассылке — что, кому, сколько отправлено."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    image_url: str | None = None
    segment: BroadcastSegment
    segment_days: int | None = None
    status: BroadcastStatus
    total_count: int
    sent_count: int
    failed_count: int
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class BroadcastCreate(BaseModel):
    """Создание рассылки — контент и сегмент обязательны."""

    title: str
    content: str
    image_url: str | None = None
    segment: BroadcastSegment = BroadcastSegment.all
    segment_days: int | None = None

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Контент не должен превышать лимит Telegram (4096 символов для текста, 1024 для caption)."""
        if len(v) > 4096:
            raise ValueError("Текст рассылки не должен превышать 4096 символов")
        return v

    @field_validator("segment_days")
    @classmethod
    def validate_segment_days(cls, v: int | None, info) -> int | None:
        """Если сегмент recent/inactive — нужно указать кол-во дней."""
        if v is not None and v <= 0:
            raise ValueError("Количество дней должно быть положительным")
        return v


class BroadcastListResponse(BaseModel):
    """Список рассылок с пагинацией."""

    model_config = ConfigDict(from_attributes=True)

    items: list[BroadcastResponse]
    total: int
    page: int
    size: int
