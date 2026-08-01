"""Схемы для бронирований — записи клиентов на услуги."""

from datetime import date, datetime, time
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class BookingStatus(StrEnum):
    """Статусы бронирования — весь жизненный цикл записи."""

    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class BookingResponse(BaseModel):
    """Полная инфа о бронировании — клиент, услуга, время, статус."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    client_name: str | None = None
    service_id: UUID
    service_name: str | None = None
    booking_date: date
    start_time: time
    end_time: time
    status: BookingStatus
    notes: str | None = None
    created_at: datetime


class BookingCreate(BaseModel):
    """Создание бронирования — кто, что, когда."""

    client_id: UUID
    service_id: UUID
    booking_date: date
    start_time: time
    end_time: time
    notes: str | None = None

    @model_validator(mode="after")
    def validate_times(self) -> "BookingCreate":
        """Время начала должно быть раньше времени окончания — иначе бред какой-то."""
        if self.start_time >= self.end_time:
            raise ValueError("Время начала записи должно быть раньше времени окончания")
        return self


class BookingStatusUpdate(BaseModel):
    """Обновление статуса бронирования — только статус, больше ничего."""

    status: BookingStatus


class BookingListResponse(BaseModel):
    """Список бронирований с пагинацией — стандартная обертка."""

    model_config = ConfigDict(from_attributes=True)

    items: list[BookingResponse]
    total: int
    page: int
    size: int
