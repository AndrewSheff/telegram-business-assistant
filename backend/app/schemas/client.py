"""Схемы для клиентов из Telegram — те самые люди, которые пишут боту."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClientResponse(BaseModel):
    """Инфа о клиенте — все что знаем из телеги + наши заметки."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telegram_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None
    notes: str | None = None
    is_blocked: bool
    last_interaction_at: datetime | None = None
    created_at: datetime
    bookings_count: int | None = None


class ClientUpdate(BaseModel):
    """Обновление клиента — заметки, блокировка, телефон."""

    notes: str | None = None
    is_blocked: bool | None = None
    phone: str | None = None


class ClientListResponse(BaseModel):
    """Список клиентов с пагинацией — стандартная обертка."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ClientResponse]
    total: int
    page: int
    size: int
