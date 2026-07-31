"""
Лог рассылки — запись об отправке конкретному клиенту.
Трекаем статус: pending -> sent/failed.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BroadcastLog(BaseModel):
    """
    Одна запись лога рассылки — результат отправки одному клиенту.
    Если упало — сохраняем текст ошибки.
    """

    __tablename__ = "broadcast_logs"

    # К какой рассылке относится
    broadcast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("broadcasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Какому клиенту отправляли
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Статус отправки
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # Текст ошибки — если status = failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Когда фактически отправили
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Связь с рассылкой
    broadcast: Mapped["Broadcast"] = relationship(  # noqa: F821
        back_populates="logs", lazy="selectin"
    )

    # Связь с клиентом
    client: Mapped["Client"] = relationship(  # noqa: F821
        back_populates="broadcast_logs", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed')",
            name="ck_broadcast_logs_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<BroadcastLog broadcast={self.broadcast_id} [{self.status}]>"
