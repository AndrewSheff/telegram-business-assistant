"""
Хендлеры для /start, /help и возврата в меню.
Первое что видит клиент — приветствие и главное меню.
"""

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models.client import Client
from app.services import settings_service

router = Router(name="start")
logger = structlog.get_logger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, db, client: Client, state: FSMContext):
    """
    Команда /start — приветствуем клиента.
    Берем welcome_message из настроек, если он задан.
    """
    # Чистим состояние FSM на всякий — вдруг клиент застрял в процессе записи
    await state.clear()

    # Достаем приветственное сообщение из настроек
    settings = await settings_service.get_settings(db)
    welcome_text = settings.welcome_message or (
        f"Привет, {client.first_name}! Добро пожаловать.\n"
        "Выбери, что тебя интересует:"
    )

    # Подставляем имя клиента если есть плейсхолдер
    welcome_text = welcome_text.replace("{name}", client.first_name)

    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
    )
    logger.info("start_command", telegram_id=client.telegram_id)


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    """Команда /help — краткая справка по возможностям бота."""
    await state.clear()

    help_text = (
        "Что умеет этот бот:\n\n"
        "Записаться — запись на услугу\n"
        "Наши услуги — посмотреть список услуг и цены\n"
        "Мои записи — посмотреть свои записи\n"
        "Задать вопрос — ответы на частые вопросы и AI-помощник\n"
        "Связаться с нами — связь с оператором\n\n"
        "Команды:\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/cancel — отмена текущего действия"
    )

    await message.answer(help_text, reply_markup=main_menu_keyboard())


@router.message(F.text == "Назад в меню")
async def back_to_menu_text(message: Message, state: FSMContext):
    """Кнопка «Назад в меню» — возвращаем в главное меню."""
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Инлайн-кнопка «Назад в меню» — аналогично, но через коллбэк."""
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
