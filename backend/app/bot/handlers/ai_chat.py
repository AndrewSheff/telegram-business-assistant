"""
Хендлер для AI-чата — обрабатывает свободные текстовые вопросы.
Вызывает ai_service для генерации ответа, логирует в chat_messages.
Если AI считает что нужен оператор — предлагает хендофф.
"""

import structlog
from aiogram import Router
from aiogram.types import Message

from app.bot.keyboards.common import handoff_keyboard
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models.client import Client
from app.services import ai_service, chat_service

# Лимит Telegram на длину сообщения — 4096 символов
TELEGRAM_MESSAGE_LIMIT = 4096

router = Router(name="ai_chat")
logger = structlog.get_logger(__name__)


@router.message()
async def handle_free_text(message: Message, db, client: Client):
    """
    Ловим все текстовые сообщения, которые не попали в другие хендлеры.
    Отправляем в AI, показываем typing пока думаем.
    """
    if not message.text:
        # Не текст — фото, стикер и т.д. — пропускаем
        await message.answer(
            "Я пока умею работать только с текстом. Напиши свой вопрос словами.",
            reply_markup=main_menu_keyboard(),
        )
        return

    user_text = message.text.strip()
    if not user_text:
        return

    # Логируем сообщение клиента
    await chat_service.log_message(
        client_id=client.id,
        role="user",
        content=user_text,
        is_handoff=False,
        db=db,
    )

    # Показываем что бот «печатает»
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing",
    )

    try:
        # Генерируем ответ через AI
        ai_response = await ai_service.generate_answer(
            question=user_text,
            db=db,
            client_id=client.id,
        )

        response_text = ai_response.get("answer", "Не удалось получить ответ.")
        should_handoff = ai_response.get("should_handoff", False)

        # Логируем ответ бота
        await chat_service.log_message(
            client_id=client.id,
            role="bot",
            content=response_text,
            is_handoff=False,
            db=db,
        )

        if should_handoff:
            # AI считает что нужен оператор — предлагаем хендофф
            await _send_long_message(message, response_text, reply_markup=handoff_keyboard())
        else:
            await _send_long_message(message, response_text)

    except Exception as e:
        logger.error("ai_service_error", error=str(e))

        # AI сломался — предлагаем связаться с оператором
        fallback_text = (
            "Извини, сейчас не могу обработать твой вопрос. "
            "Попробуй позже или свяжись с оператором."
        )

        await chat_service.log_message(
            client_id=client.id,
            role="bot",
            content=fallback_text,
            is_handoff=False,
            db=db,
        )

        await message.answer(fallback_text, reply_markup=handoff_keyboard())


async def _send_long_message(message: Message, text: str, reply_markup=None):
    """
    Отправляем длинное сообщение — если превышает лимит Telegram,
    разбиваем на части. Клавиатуру цепляем только к последней части.
    """
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        await message.answer(text, reply_markup=reply_markup)
        return

    # Разбиваем по абзацам, если не помещается — по лимиту
    parts = []
    while text:
        if len(text) <= TELEGRAM_MESSAGE_LIMIT:
            parts.append(text)
            break
        # Ищем последний перенос строки в пределах лимита
        cut_at = text.rfind("\n", 0, TELEGRAM_MESSAGE_LIMIT)
        if cut_at <= 0:
            cut_at = TELEGRAM_MESSAGE_LIMIT
        parts.append(text[:cut_at])
        text = text[cut_at:].lstrip("\n")

    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        await message.answer(part, reply_markup=reply_markup if is_last else None)
