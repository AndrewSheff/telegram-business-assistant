"""
Сообщение в чате — хранит историю переписки клиента с ботом/оператором.
Роли: user (клиент), bot (AI-бот), operator (живой оператор).
"""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ChatMessage(BaseModel):
    """
    Одно сообщение в чате.
    Храним все подряд — и от клиента, и от бота, и от оператора.
    """

    __tablename__ = "chat_messages"

    # Какому клиенту принадлежит сообщение
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Кто написал: user, bot или operator
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Текст сообщения
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Флаг передачи диалога оператору (handoff)
    is_handoff: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Связь с клиентом
    client: Mapped["Client"] = relationship(  # noqa: F821
        back_populates="messages", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'bot', 'operator')",
            name="ck_chat_messages_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage [{self.role}] {self.content[:40]}...>"
