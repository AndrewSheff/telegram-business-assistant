"""Схемы для услуг и категорий — то, что бизнес предлагает клиентам."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ServiceResponse(BaseModel):
    """Полная инфа об услуге, включая название категории если есть."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    duration_minutes: int
    category_id: UUID | None = None
    category_name: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime


class ServiceCreate(BaseModel):
    """Создание услуги — название и цена обязательны, остальное по желанию."""

    name: str
    description: str | None = None
    price: Decimal
    duration_minutes: int
    category_id: UUID | None = None
    sort_order: int | None = 0

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Название услуги не может быть пустым — это ж что получится-то."""
        if not v or not v.strip():
            raise ValueError("Название услуги не может быть пустым")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        """Цена не может быть отрицательной, ну камон."""
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v

    @field_validator("duration_minutes")
    @classmethod
    def duration_must_be_positive(cls, v: int) -> int:
        """Длительность должна быть больше нуля, логично же."""
        if v <= 0:
            raise ValueError("Длительность должна быть больше нуля")
        return v


class ServiceUpdate(BaseModel):
    """Обновление услуги — меняем только то что пришло."""

    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    duration_minutes: int | None = None
    category_id: UUID | None = None
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        """Цена не может быть отрицательной даже при обновлении."""
        if v is not None and v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v

    @field_validator("duration_minutes")
    @classmethod
    def duration_must_be_positive(cls, v: int | None) -> int | None:
        """Длительность все ещё должна быть больше нуля."""
        if v is not None and v <= 0:
            raise ValueError("Длительность должна быть больше нуля")
        return v


class CategoryResponse(BaseModel):
    """Категория услуг — простая штука: имя и порядок сортировки."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sort_order: int


class CategoryCreate(BaseModel):
    """Создание категории — только название нужно, порядок опционально."""

    name: str
    sort_order: int | None = 0


class CategoryUpdate(BaseModel):
    """Обновление категории — название и/или порядок."""

    name: str | None = None
    sort_order: int | None = None
