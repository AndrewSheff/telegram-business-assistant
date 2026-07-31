"""Схемы для расписания — рабочие часы, исключения, слоты."""

from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class WorkingHoursResponse(BaseModel):
    """Рабочие часы на конкретный день недели — когда работаем, когда обед."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    break_start: time | None = None
    break_end: time | None = None
    is_working_day: bool


class WorkingHoursUpdate(BaseModel):
    """Обновление рабочих часов — день недели обязателен, остальное зависит от ситуации."""

    day_of_week: int
    start_time: time
    end_time: time
    break_start: time | None = None
    break_end: time | None = None
    is_working_day: bool = True

    @field_validator("day_of_week")
    @classmethod
    def valid_day_of_week(cls, v: int) -> int:
        """День недели от 0 (пн) до 6 (вс), другого не дано."""
        if v < 0 or v > 6:
            raise ValueError("День недели должен быть от 0 (понедельник) до 6 (воскресенье)")
        return v

    @model_validator(mode="after")
    def validate_times(self) -> "WorkingHoursUpdate":
        """Проверяем что время начала раньше конца и перерыв корректный."""
        if self.is_working_day and self.start_time >= self.end_time:
            raise ValueError("Время начала должно быть раньше времени окончания")
        if self.break_start and self.break_end:
            if self.break_start >= self.break_end:
                raise ValueError("Начало перерыва должно быть раньше окончания")
        elif self.break_start and not self.break_end:
            raise ValueError("Указано начало перерыва, но не указан конец")
        elif not self.break_start and self.break_end:
            raise ValueError("Указан конец перерыва, но не указано начало")
        return self


class ScheduleExceptionResponse(BaseModel):
    """Исключение в расписании — выходной, сокращенный день и т.п."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exception_date: date
    is_working_day: bool
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None


class ScheduleExceptionCreate(BaseModel):
    """Создание исключения — дата обязательна, время если рабочий день."""

    exception_date: date
    is_working_day: bool = False
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_working_day_times(self) -> "ScheduleExceptionCreate":
        """Если рабочий день — нужно время, если выходной — не нужно."""
        if self.is_working_day:
            if not self.start_time or not self.end_time:
                raise ValueError(
                    "Для рабочего дня-исключения нужно указать время начала и окончания"
                )
            if self.start_time >= self.end_time:
                raise ValueError("Время начала должно быть раньше времени окончания")
        return self


class TimeSlot(BaseModel):
    """Временной слот — просто отрезок времени, без лишних заморочек."""

    start_time: time
    end_time: time
