"""
Хендлеры для FAQ — часто задаваемые вопросы.
Сначала показываем FAQ, если ответа нет — предлагаем задать вопрос AI.
"""

import uuid

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards.common import handoff_keyboard
from app.services import faq_service

router = Router(name="faq")
logger = structlog.get_logger(__name__)


@router.message(F.text == "Задать вопрос")
async def show_faq_list(message: Message, db):
    """
    Кнопка «Задать вопрос» — показываем список FAQ.
    Группируем по категориям если они есть, плюс кнопка для свободного вопроса.
    """
    faq_items = await faq_service.list_faq(db, active_only=True)

    if not faq_items:
        # FAQ пусто — сразу предлагаем задать вопрос
        await message.answer(
            "Напиши свой вопрос, и я постараюсь помочь:",
            reply_markup=handoff_keyboard(),
        )
        return

    # Группируем по категориям
    categories: dict[str | None, list] = {}
    for item in faq_items:
        cat = item.category or "Общее"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    buttons = []
    for category_name, items in categories.items():
        # Заголовок категории (если больше одной)
        if len(categories) > 1:
            buttons.append([
                InlineKeyboardButton(
                    text=f"--- {category_name} ---",
                    callback_data="ignore",
                )
            ])

        for item in items:
            # Обрезаем вопрос если слишком длинный для кнопки
            question_text = item.question[:60]
            if len(item.question) > 60:
                question_text += "..."

            buttons.append([
                InlineKeyboardButton(
                    text=question_text,
                    callback_data=f"faq:{item.id}",
                )
            ])

    # Кнопка «Задать свой вопрос» — для AI
    buttons.append([
        InlineKeyboardButton(
            text="Задать свой вопрос",
            callback_data="ask_ai",
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "Часто задаваемые вопросы:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("faq:"))
async def show_faq_answer(callback: CallbackQuery, db):
    """Показываем ответ на выбранный FAQ."""
    faq_id_str = callback.data.split(":")[1]

    try:
        faq_id = uuid.UUID(faq_id_str)
    except ValueError:
        await callback.answer("Некорректный вопрос")
        return

    try:
        faq_item = await faq_service.get_faq(faq_id, db)
    except Exception:
        await callback.answer("Вопрос не найден")
        return

    # Обрезаем ответ если он слишком длинный для Telegram (4096 символов)
    answer_text = faq_item.answer
    max_answer_len = 4096 - len(faq_item.question) - 20  # запас на HTML-теги и разметку
    if len(answer_text) > max_answer_len:
        answer_text = answer_text[:max_answer_len - 3] + "..."

    text = (
        f"<b>{faq_item.question}</b>\n\n"
        f"{answer_text}"
    )

    # Кнопки — задать ещё вопрос или связаться
    answer_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Другие вопросы",
                    callback_data="show_faq_list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Задать свой вопрос",
                    callback_data="ask_ai",
                ),
            ],
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=answer_keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "show_faq_list")
async def back_to_faq_list(callback: CallbackQuery, db):
    """Возврат к списку FAQ — через инлайн-кнопку."""
    faq_items = await faq_service.list_faq(db, active_only=True)

    if not faq_items:
        await callback.message.edit_text(
            "Напиши свой вопрос, и я постараюсь помочь:",
        )
        await callback.answer()
        return

    buttons = []
    categories: dict[str | None, list] = {}
    for item in faq_items:
        cat = item.category or "Общее"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    for category_name, items in categories.items():
        if len(categories) > 1:
            buttons.append([
                InlineKeyboardButton(
                    text=f"--- {category_name} ---",
                    callback_data="ignore",
                )
            ])
        for item in items:
            question_text = item.question[:60]
            if len(item.question) > 60:
                question_text += "..."
            buttons.append([
                InlineKeyboardButton(
                    text=question_text,
                    callback_data=f"faq:{item.id}",
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="Задать свой вопрос",
            callback_data="ask_ai",
        )
    ])

    await callback.message.edit_text(
        "Часто задаваемые вопросы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data == "ask_ai")
async def prompt_ai_question(callback: CallbackQuery):
    """Предлагаем написать вопрос для AI — просто текстом в чат."""
    await callback.message.edit_text(
        "Напиши свой вопрос, и я постараюсь помочь.\n"
        "Для возврата в меню нажми /start"
    )
    await callback.answer()
