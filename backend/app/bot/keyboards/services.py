"""
Клавиатуры для работы с услугами — список услуг и детали конкретной услуги.
Все на инлайн-кнопках, чтобы было аккуратненько.
"""

import uuid

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def services_keyboard(services: list) -> InlineKeyboardMarkup:
    """
    Список услуг в виде инлайн-кнопок.
    Каждая кнопка — одна услуга, callback_data = "service:{id}".
    """
    buttons = []
    for service in services:
        buttons.append([
            InlineKeyboardButton(
                text=f"{service.name} — {service.price:.0f} р.",
                callback_data=f"service:{service.id}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_detail_keyboard(service_id: uuid.UUID) -> InlineKeyboardMarkup:
    """
    Детали услуги — кнопка записаться и назад к списку.
    Просто и понятно для клиента.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Записаться",
                    callback_data=f"book:{service_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_services",
                ),
            ],
        ]
    )
