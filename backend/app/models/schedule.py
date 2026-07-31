"""
Рабочее расписание — по дням недели.
0 = понедельник, 6 = воскресенье.
Можно задать перерыв (обед и т.п.).
"""

from datetime import time

from sqlalchemy import CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class WorkingHours(BaseModel):
    """
    Расписание работы на конкретный день недели.
    Один день — одна запись, дубликатов быть не должно.
    """

    __tablename__ = "working_hours"

    # День недели: 0 (пн) — 6 (вс)
    day_of_week: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )

    # Время начала рабочего дня
    start_time: Mapped[time] = mapped_column(nullable=False)

    # Время конца рабочего дня
    end_time: Mapped[time] = mapped_column(nullable=False)

    # Начало перерыва — если есть
    break_start: Mapped[time | None] = mapped_column(nullable=True)

    # Конец перерыва
    break_end: Mapped[time | None] = mapped_column(nullable=True)

    # Рабочий ли это день вообще
    is_working_day: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_working_hours_day_of_week",
        ),
    )

    def __repr__(self) -> str:
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        day_name = days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "?"
        return f"<WorkingHours {day_name} {self.start_time}-{self.end_time}>"
