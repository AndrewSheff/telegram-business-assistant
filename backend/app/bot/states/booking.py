"""
Состояния FSM для процесса записи на услугу.
Клиент проходит шаги: выбор услуги -> дата -> время -> подтверждение.
"""

from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    """Цепочка состояний для записи — идем последовательно от услуги до подтверждения."""

    # Выбираем услугу из списка
    choosing_service = State()

    # Выбираем дату из календаря
    choosing_date = State()

    # Выбираем время из свободных слотов
    choosing_time = State()

    # Подтверждаем или отменяем запись
    confirming = State()
