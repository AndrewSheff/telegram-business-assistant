"""
Клавиатура главного меню — показываем кнопки внизу экрана.
Это reply-клавиатура, она остается на месте пока не сменим.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Собираем главное меню — три ряда кнопок, resize чтобы не было огромным."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Записаться"),
                KeyboardButton(text="Наши услуги"),
            ],
            [
                KeyboardButton(text="Мои записи"),
                KeyboardButton(text="Задать вопрос"),
            ],
            [
                KeyboardButton(text="Связаться с нами"),
            ],
        ],
        resize_keyboard=True,
    )
    return keyboard
