"""
Блоки знаний — куски текста, которые AI использует как контекст.
Например: «О компании», «Правила отмены», «Как добраться».
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class KnowledgeBlock(BaseModel):
    """
    Блок знаний — кусочек контекста для AI.
    Владелец бизнеса заполняет, AI подтягивает при ответах.
    """

    __tablename__ = "knowledge_blocks"

    # Заголовок блока — «О нас», «Как добраться» и т.д.
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Содержимое — основной текст
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Активен ли блок
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Порядок сортировки
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<KnowledgeBlock {self.title}>"
