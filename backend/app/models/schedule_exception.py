"""
Исключения из расписания — праздники, выходные, спец. рабочие дни.
Перекрывает обычное расписание на конкретную дату.
"""

from datetime import date, time

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ScheduleException(BaseModel):
    """
    Исключение из обычного расписания.
    Например, 8 марта — выходной, или суббота — внезапно рабочая.
    """

    __tablename__ = "schedule_exceptions"

    # Дата исключения — уникальна, на одну дату одно исключение
    exception_date: Mapped[date] = mapped_column(
        Date, unique=True, nullable=False, index=True
    )

    # Рабочий ли этот день (True = работаем, False = отдыхаем)
    is_working_day: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Если рабочий — во сколько начинаем
    start_time: Mapped[time | None] = mapped_column(nullable=True)

    # Если рабочий — во сколько заканчиваем
    end_time: Mapped[time | None] = mapped_column(nullable=True)

    # Причина — «праздник», «корпоратив», «отпуск» и т.п.
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        status = "рабочий" if self.is_working_day else "выходной"
        return f"<ScheduleException {self.exception_date} ({status})>"
