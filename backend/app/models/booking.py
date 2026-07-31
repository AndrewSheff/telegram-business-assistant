"""
Модель записи/бронирования — клиент записывается на услугу.
Статусы: pending -> confirmed -> completed/cancelled/no_show.
"""

import uuid
from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Booking(BaseModel):
    """
    Запись клиента на услугу.
    Содержит дату, время, статус и флаги отправки напоминаний.
    """

    __tablename__ = "bookings"

    # Кто записался
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # На какую услугу
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Дата записи
    booking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Время начала
    start_time: Mapped[time] = mapped_column(nullable=False)

    # Время окончания (start_time + duration_minutes услуги)
    end_time: Mapped[time] = mapped_column(nullable=False)

    # Статус записи
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )

    # Заметки к записи — доп. пожелания клиента или оператора
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Отправлено ли напоминание за 24 часа
    reminder_24h_sent: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Отправлено ли напоминание за 2 часа
    reminder_2h_sent: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Связь с клиентом
    client: Mapped["Client"] = relationship(  # noqa: F821
        back_populates="bookings", lazy="selectin"
    )

    # Связь с услугой
    service: Mapped["Service"] = relationship(  # noqa: F821
        back_populates="bookings", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'completed', 'cancelled', 'no_show')",
            name="ck_bookings_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Booking {self.booking_date} {self.start_time} [{self.status}]>"
