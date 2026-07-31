"""
Хендлеры для передачи диалога оператору (handoff).
Когда бот не справляется — клиент может позвать живого человека.
В режиме хендоффа все сообщения клиента пишутся в чат для оператора.
"""

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models.client import Client
from app.services import chat_service, settings_service

router = Router(name="handoff")
logger = structlog.get_logger(__name__)


@router.message(F.text == "Связаться с нами")
async def contact_us(message: Message, db, client: Client):
    """
    Кнопка «Связаться с нами» — начинаем хендофф.
    Логируем запрос и говорим клиенту ждать.
    """
    await _initiate_handoff(message, db, client)


@router.callback_query(F.data == "handoff")
async def handoff_callback(callback: CallbackQuery, db, client: Client):
    """Инлайн-кнопка хендоффа — из ответа AI или откуда-нибудь ещё."""
    await _initiate_handoff(callback.message, db, client, from_callback=True)
    await callback.answer()


async def _initiate_handoff(
    message: Message,
    db,
    client: Client,
    from_callback: bool = False,
):
    """
    Общая логика хендоффа — логируем сообщение с флагом is_handoff=True.
    Оператор увидит это в админке и ответит.
    """
    # Достаем контактную инфу из настроек
    settings = await settings_service.get_settings(db)

    # Логируем хендофф-сообщение
    await chat_service.log_message(
        client_id=client.id,
        role="user",
        content="[Клиент запросил связь с оператором]",
        is_handoff=True,
        db=db,
    )

    # Формируем ответ с контактами если есть
    contact_parts = ["Оператор скоро ответит. Подожди немного."]

    if settings.phone:
        contact_parts.append(f"\nТелефон: {settings.phone}")
    if settings.address:
        contact_parts.append(f"Адрес: {settings.address}")
    if settings.website:
        contact_parts.append(f"Сайт: {settings.website}")

    contact_parts.append(
        "\nПока ждешь, можешь написать свой вопрос — оператор его увидит."
    )

    response_text = "\n".join(contact_parts)

    await message.answer(response_text, reply_markup=main_menu_keyboard())

    logger.info(
        "handoff_initiated",
        client_id=str(client.id),
        telegram_id=client.telegram_id,
    )
