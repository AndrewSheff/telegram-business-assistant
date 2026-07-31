"""
Модель услуги — то, что бизнес предлагает клиентам.
Привязана к категории, имеет цену и длительность.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Service(BaseModel):
    """
    Конкретная услуга — стрижка, маникюр, консультация и т.д.
    Цена в Numeric(10,2), длительность в минутах.
    """

    __tablename__ = "services"

    # К какой категории относится
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Название услуги
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Описание — можно подробнее расписать, что входит
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Цена — точность до копеек
    price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    # Сколько длится в минутах
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Порядок сортировки внутри категории
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Активна ли услуга — можно временно скрыть
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Связь с категорией
    category: Mapped["ServiceCategory"] = relationship(  # noqa: F821
        back_populates="services", lazy="selectin"
    )

    # Записи на эту услугу
    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        back_populates="service", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Service {self.name} ({self.price}₽)>"
