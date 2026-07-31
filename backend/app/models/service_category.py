"""
Категории услуг — группировка для удобства.
Например: «Стрижки», «Окрашивание», «Маникюр».
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ServiceCategory(BaseModel):
    """
    Категория услуг — просто название и порядок сортировки.
    Услуги привязываются к категории через FK.
    """

    __tablename__ = "service_categories"

    # Название категории
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Порядок отображения — чем меньше, тем выше
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Услуги в этой категории
    services: Mapped[list["Service"]] = relationship(  # noqa: F821
        back_populates="category", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ServiceCategory {self.name}>"
