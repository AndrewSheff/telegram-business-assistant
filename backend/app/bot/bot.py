"""
Главный модуль бота — тут собираем все вместе:
Bot, Dispatcher, мидлвари, хендлеры, запуск/остановка поллинга.
"""

import asyncio
import contextlib

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import ai_chat, booking, faq, handoff, my_bookings, services, start
from app.bot.middlewares import DatabaseMiddleware, UserRegistrationMiddleware
from app.config import settings

logger = structlog.get_logger(__name__)

# Глобальные ссылки на бота и диспетчер — нужны для start/stop
_bot: Bot | None = None
_dp: Dispatcher | None = None
_polling_task: asyncio.Task | None = None


def _create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """
    Создаем бота и диспетчер, подключаем мидлвари и роутеры.
    Все хендлеры регистрируются тут — порядок важен!
    ai_chat идет последним, потому что ловит все текстовые сообщения.
    """
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Redis для FSM — состояния выживают при рестарте бота
    try:
        storage = RedisStorage.from_url(settings.REDIS_URL)
        logger.info("fsm_storage_redis", url=settings.REDIS_URL)
    except Exception:
        # Фоллбек на память, если Redis недоступен (для разработки)
        storage = MemoryStorage()
        logger.warning("fsm_storage_memory_fallback", msg="Redis недоступен, FSM в памяти")
    dp = Dispatcher(storage=storage)

    # Мидлвари — сначала БД, потом регистрация юзера (ей нужна БД)
    dp.message.middleware(DatabaseMiddleware())
    dp.message.middleware(UserRegistrationMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(UserRegistrationMiddleware())

    # Роутеры — порядок важен!
    # start и booking первые (команды и FSM), ai_chat последний (catch-all)
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(my_bookings.router)
    dp.include_router(services.router)
    dp.include_router(faq.router)
    dp.include_router(handoff.router)
    dp.include_router(ai_chat.router)  # последний — ловит все остальное

    return bot, dp


def get_bot() -> Bot | None:
    """Геттер для экземпляра бота — нужен фоновым задачам для отправки сообщений."""
    return _bot


async def start_bot() -> None:
    """
    Запускаем бота — поллинг в фоновой asyncio-задаче.
    Если токен не задан — ругаемся в лог и не стартуем.
    """
    global _bot, _dp, _polling_task

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("telegram_bot_token_not_set", msg="Бот не запущен — токен не задан")
        return

    _bot, _dp = _create_bot_and_dispatcher()

    logger.info("starting_telegram_bot")

    # Запускаем поллинг в фоне, чтобы не блокировать FastAPI
    _polling_task = asyncio.create_task(_run_polling())


async def _run_polling() -> None:
    """Запуск поллинга — оборачиваем в try/except чтобы не ронять все приложение."""
    try:
        # Удаляем вебхук если был — на всякий случай
        await _bot.delete_webhook(drop_pending_updates=True)
        logger.info("telegram_bot_polling_started")
        await _dp.start_polling(_bot)
    except asyncio.CancelledError:
        logger.info("telegram_bot_polling_cancelled")
    except Exception as e:
        logger.error("telegram_bot_polling_error", error=str(e))


async def stop_bot() -> None:
    """
    Останавливаем бота — отменяем поллинг-задачу и закрываем сессию.
    Вызывается при shutdown приложения.
    """
    global _bot, _dp, _polling_task

    if _polling_task is not None:
        _polling_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _polling_task
        _polling_task = None

    if _dp is not None:
        await _dp.stop_polling()
        _dp = None

    if _bot is not None:
        await _bot.session.close()
        _bot = None

    logger.info("telegram_bot_stopped")
