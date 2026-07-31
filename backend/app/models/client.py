"""
Модель клиента — человек из Telegram, который общается с ботом.
Храним его telegram_id и базовую инфу из профиля.
"""

from datetime import datetime

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Client(BaseModel):
    """
    Клиент из Telegram — тот, кто пишет боту.
    telegram_id уникален, остальное подтягивается из профиля.
    """

    __tablename__ = "clients"

    # Telegram user ID — уникальный, BIGINT потому что там большие числа
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )

    # Имя из профиля Telegram
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Фамилия — может и не быть
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # @username — тоже не у всех есть
    username: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Телефон — если расшарил контакт
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Заметки оператора про клиента
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Заблокировали ли мы этого клиента
    is_blocked: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Когда последний раз писал — для сегментации рассылок
    last_interaction_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Записи на услуги
    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        back_populates="client", lazy="selectin"
    )

    # История сообщений
    messages: Mapped[list["ChatMessage"]] = relationship(  # noqa: F821
        back_populates="client", lazy="selectin"
    )

    # Логи рассылок
    broadcast_logs: Mapped[list["BroadcastLog"]] = relationship(  # noqa: F821
        back_populates="client", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Client {self.telegram_id} ({self.first_name})>"
