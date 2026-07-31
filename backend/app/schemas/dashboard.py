"""Схемы для дашборда — статистика, графики, топы."""

from datetime import date

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Основная статистика для главной страницы — все самое важное одним взглядом."""

    total_clients: int
    new_clients_week: int
    bookings_today: int
    bookings_week: int
    bookings_month: int
    pending_handoffs: int


class ActivityPoint(BaseModel):
    """Точка на графике активности — бронирования и взаимодействия за день."""

    date: date
    bookings: int
    interactions: int


class TopService(BaseModel):
    """Популярная услуга — для рейтинга самых востребованных."""

    service_name: str
    count: int


class TopQuestion(BaseModel):
    """Частый вопрос — для понимания что клиентов интересует больше всего."""

    question: str
    count: int
