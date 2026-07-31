"""Схемы для чата — сообщения, ответы оператора, хендоффы."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatMessageResponse(BaseModel):
    """Сообщение в чате — от клиента, бота или оператора."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    role: str
    content: str
    is_handoff: bool
    created_at: datetime


class OperatorReplyRequest(BaseModel):
    """Ответ оператора клиенту — просто текст, ничего лишнего."""

    content: str


class HandoffClientResponse(BaseModel):
    """Клиент, ожидающий ответа оператора — самое важное для очереди."""

    model_config = ConfigDict(from_attributes=True)

    client_id: UUID
    client_name: str
    telegram_username: str | None = None
    last_message: str | None = None
    unread_count: int
    created_at: datetime
