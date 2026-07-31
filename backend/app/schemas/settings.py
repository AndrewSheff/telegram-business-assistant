"""Схемы для настроек бизнеса — все конфиги бота и AI в одном месте."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class SettingsResponse(BaseModel):
    """Настройки бизнеса — бот-токен скрыт, показываем только факт наличия."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bot_token_set: bool
    business_name: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    welcome_message: str | None = None
    offline_message: str | None = None
    timezone: str
    min_cancel_hours: int
    ai_model: str | None = None
    ai_system_prompt: str | None = None
    updated_at: datetime


class SettingsUpdate(BaseModel):
    """Обновление настроек — все опционально, меняем только нужное."""

    bot_token: str | None = None
    business_name: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    welcome_message: str | None = None
    offline_message: str | None = None
    timezone: str | None = None
    min_cancel_hours: int | None = None
    ai_model: str | None = None
    ai_system_prompt: str | None = None

    @field_validator("min_cancel_hours")
    @classmethod
    def validate_min_cancel_hours(cls, v: int | None) -> int | None:
        """Минимум часов для отмены не может быть отрицательным, это ж время."""
        if v is not None and v < 0:
            raise ValueError("Минимальное время для отмены не может быть отрицательным")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        """Проверяем что таймзона вменяемая."""
        if v is not None:
            import zoneinfo
            try:
                zoneinfo.ZoneInfo(v)
            except (KeyError, zoneinfo.ZoneInfoNotFoundError) as err:
                raise ValueError(f"Неизвестная таймзона: {v}") from err
        return v
