"""
Рассылки — массовая отправка сообщений клиентам.
Можно сегментировать: всем, недавним, неактивным.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Broadcast(BaseModel):
    """
    Рассылка сообщений клиентам.
    Создается через админку, отправляется фоновой задачей.
    """

    __tablename__ = "broadcasts"

    # Название рассылки — для удобства в админке
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Текст рассылки
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Картинка — если нужна (URL)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Сегмент: all — всем, recent — недавним, inactive — давно не писали
    segment: Mapped[str] = mapped_column(
        String(20), nullable=False, default="all"
    )

    # Кол-во дней для сегмента (recent = за N дней, inactive = не писали N дней)
    segment_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Статус рассылки
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )

    # Сколько всего получателей
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Сколько успешно отправлено
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Сколько упало с ошибкой
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Когда запланирована отправка (если отложенная)
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Когда завершилась отправка
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Кто создал рассылку
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Связь с создателем
    creator: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="broadcasts", lazy="selectin"
    )

    # Логи отправки
    logs: Mapped[list["BroadcastLog"]] = relationship(  # noqa: F821
        back_populates="broadcast", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "segment IN ('all', 'recent', 'inactive')",
            name="ck_broadcasts_segment",
        ),
        CheckConstraint(
            "status IN ('draft', 'sending', 'completed', 'failed')",
            name="ck_broadcasts_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Broadcast {self.title} [{self.status}]>"
