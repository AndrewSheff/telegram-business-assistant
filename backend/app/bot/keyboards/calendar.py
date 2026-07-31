"""
Инлайн-календарь для выбора даты записи.
Показываем доступные даты на ближайшие 14 дней, группируем по неделям.
"""

from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Названия дней недели — коротко и по-русски
DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def calendar_keyboard(available_dates: list[date]) -> InlineKeyboardMarkup:
    """
    Генерируем инлайн-календарь с доступными датами.
    Недоступные даты показываем как пустышки (пробел), доступные — кнопками.
    Максимум 14 дней вперед, группировка по неделям.
    """
    if not available_dates:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Нет доступных дат", callback_data="no_dates")]
            ]
        )

    available_set = set(available_dates)

    # Берем диапазон от первой до последней доступной даты
    min_date = min(available_dates)
    max_date = max(available_dates)

    # Заголовок с названиями дней
    header_row = [
        InlineKeyboardButton(text=name, callback_data="ignore")
        for name in DAY_NAMES
    ]

    rows = [header_row]

    # Генерируем строки по неделям
    current = min_date
    # Откатываемся к понедельнику текущей недели
    weekday_offset = current.weekday()
    from datetime import timedelta
    week_start = current - timedelta(days=weekday_offset)

    while week_start <= max_date:
        row = []
        for day_offset in range(7):
            cell_date = week_start + timedelta(days=day_offset)

            if cell_date in available_set:
                # Доступная дата — делаем кнопку
                row.append(
                    InlineKeyboardButton(
                        text=str(cell_date.day),
                        callback_data=f"date:{cell_date.isoformat()}",
                    )
                )
            else:
                # Недоступная или не в диапазоне — пустышка
                row.append(
                    InlineKeyboardButton(text=" ", callback_data="ignore")
                )

        rows.append(row)
        week_start += timedelta(days=7)

    # Кнопка отмены внизу
    rows.append([
        InlineKeyboardButton(text="Отмена", callback_data="cancel_booking")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
