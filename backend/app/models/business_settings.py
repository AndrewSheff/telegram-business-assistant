"""
Настройки бизнеса — синглтон, одна строка на всю базу.
Тут токен бота, название, адрес, приветственное сообщение и т.д.
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BusinessSettings(BaseModel):
    """
    Настройки бизнеса — всегда одна запись в таблице.
    Хранит все конфигурируемые параметры бота и бизнеса.
    """

    __tablename__ = "business_settings"

    # Токен Telegram-бота
    bot_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Название бизнеса — отображается клиентам
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Описание бизнеса
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Адрес — куда приходить
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Телефон для связи
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Сайт
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Приветственное сообщение для новых клиентов
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Сообщение вне рабочего времени
    offline_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Часовой пояс бизнеса
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UTC"
    )

    # За сколько часов можно отменить запись (минимум)
    min_cancel_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=24
    )

    # Какую AI-модель используем
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Системный промпт для AI
    ai_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<BusinessSettings {self.business_name or 'не настроено'}>"
