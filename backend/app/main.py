"""
Точка входа FastAPI-приложения — тут собираем все вместе:
роутеры, мидлвари, лайфсайкл и прочие радости.
"""

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Роутеры — каждый модуль со своим префиксом и тегами
from app.api.v1.auth import router as auth_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.broadcasts import router as broadcasts_router
from app.api.v1.chat import router as chat_router
from app.api.v1.clients import router as clients_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.faq import router as faq_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.schedule import router as schedule_router
from app.api.v1.services_mgmt import router as services_router
from app.api.v1.settings import router as settings_router
from app.api.v1.users import router as users_router
from app.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.database import async_session

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Лайфсайкл приложения — тут инициализируем все что нужно при старте
    и аккуратно прибираем при остановке.
    """
    # -- Startup --
    setup_logging()
    logger.info("app_starting", version="1.0.0")

    # Проверяем что SECRET_KEY был изменен — дефолтный = дыра в безопасности
    from app.config import _DEV_SECRET
    if settings.SECRET_KEY == _DEV_SECRET:
        logger.warning(
            "insecure_secret_key",
            msg="SECRET_KEY не изменен! Используется дефолтное значение. "
                "Обязательно смените в .env перед деплоем в прод.",
        )

    # Создаем начального админа и дефолтные данные
    async with async_session() as db:
        from app.services.auth_service import create_initial_admin
        from app.services.schedule_service import init_default_schedule
        from app.services.settings_service import get_settings

        await create_initial_admin(db)
        await init_default_schedule(db)
        await get_settings(db)

    # Запускаем Telegram-бота — может быть не настроен, не падаем
    bot_started = False
    try:
        from app.bot.bot import start_bot, stop_bot
        await start_bot()
        bot_started = True
        logger.info("telegram_bot_started")
    except Exception as exc:
        logger.warning("telegram_bot_start_failed", error=str(exc))

    # Запускаем планировщик фоновых задач — тоже может быть не готов
    scheduler_started = False
    try:
        from app.tasks.scheduler import start_scheduler, stop_scheduler
        await start_scheduler()
        scheduler_started = True
        logger.info("scheduler_started")
    except Exception as exc:
        logger.warning("scheduler_start_failed", error=str(exc))

    logger.info("app_started")

    yield

    # -- Shutdown --
    logger.info("app_shutting_down")

    if bot_started:
        try:
            await stop_bot()
            logger.info("telegram_bot_stopped")
        except Exception as exc:
            logger.warning("telegram_bot_stop_failed", error=str(exc))

    if scheduler_started:
        try:
            await stop_scheduler()
            logger.info("scheduler_stopped")
        except Exception as exc:
            logger.warning("scheduler_stop_failed", error=str(exc))

    logger.info("app_stopped")


# Создаем приложение
app = FastAPI(
    title="Telegram Business Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# -- CORS --
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Rate limiter (slowapi) --
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# -- Мидлварь для Request ID --
@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:
    """
    Генерируем уникальный ID для каждого запроса — удобно для дебага.
    Прокидываем в structlog через contextvars и в заголовок ответа.
    """
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# -- Мидлварь для логирования запросов --
@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    """
    Логируем каждый запрос — метод, путь, статус, время выполнения.
    Полезно для мониторинга и отлова тормозов.
    """
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    return response


# -- Подключаем роутеры --
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(services_router)          # уже имеет /api/v1/services
app.include_router(schedule_router)          # уже имеет /api/v1/schedule
app.include_router(bookings_router)          # уже имеет /api/v1/bookings
app.include_router(clients_router, prefix="/api/v1")
app.include_router(faq_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(broadcasts_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
