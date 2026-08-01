"""Схемы для пользователей системы (владелец, оператор)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRole(StrEnum):
    """Роли в системе — пока только владелец и оператор."""

    owner = "owner"
    operator = "operator"


class UserResponse(BaseModel):
    """Полная инфа о пользователе для ответов API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    must_change_password: bool
    created_at: datetime


class UserCreate(BaseModel):
    """Создание нового пользователя — email обязательно уникальный."""

    email: EmailStr
    name: str
    role: UserRole = UserRole.operator


class UserUpdate(BaseModel):
    """Обновление пользователя — все поля опциональные, меняем только то что надо."""

    name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class ProfileUpdate(BaseModel):
    """Обновление своего профиля — пока можно менять только имя."""

    name: str
