"""
Общие клавиатуры — слоты времени, подтверждение, назад в меню, хендофф.
Переиспользуются в разных хендлерах.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def time_slots_keyboard(slots: list) -> InlineKeyboardMarkup:
    """
    Сетка временных слотов — показываем начало каждого слота.
    По 3 кнопки в ряд чтобы не было каши.
    """
    buttons = []
    row: list[InlineKeyboardButton] = []

    for slot in slots:
        time_str = slot.start_time.strftime("%H:%M")
        row.append(
            InlineKeyboardButton(
                text=time_str,
                callback_data=f"time:{time_str}",
            )
        )
        # По 3 кнопки в ряд — выглядит аккуратно
        if len(row) == 3:
            buttons.append(row)
            row = []

    # Добавляем остаток если не кратно 3
    if row:
        buttons.append(row)

    # Кнопка отмены внизу
    buttons.append([
        InlineKeyboardButton(text="Отмена", callback_data="cancel_booking")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_booking_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение записи — да или нет, третьего не дано."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить",
                    callback_data="confirm_booking",
                ),
                InlineKeyboardButton(
                    text="Отменить",
                    callback_data="cancel_booking",
                ),
            ],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню — используется когда показываем инфу."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data="back_to_menu",
                ),
            ],
        ]
    )


def handoff_keyboard() -> InlineKeyboardMarkup:
    """Кнопка связи с оператором — когда бот не справляется."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Связаться с оператором",
                    callback_data="handoff",
                ),
            ],
        ]
    )
