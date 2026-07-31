"""
FAQ — часто задаваемые вопросы.
Бот использует их для ответов, чтобы не дергать AI на типовые вопросы.
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class FaqItem(BaseModel):
    """
    Элемент FAQ — пара вопрос/ответ.
    Можно сгруппировать по категориям и отсортировать.
    """

    __tablename__ = "faq_items"

    # Вопрос — что спрашивают
    question: Mapped[str] = mapped_column(Text, nullable=False)

    # Ответ — что отвечаем
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Категория — для группировки (например, «Оплата», «Доставка»)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Порядок сортировки
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Активен ли — можно временно скрыть без удаления
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<FaqItem {self.question[:50]}...>"
