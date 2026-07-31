"""
Health-check эндпоинт — проверяем что все компоненты живы.
Публичный, без авторизации — удобно для мониторинга и балансировщиков.
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import async_session

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    Проверка здоровья сервиса.
    Чекаем: БД, Redis, конфигурацию Telegram-бота и AI-провайдера.
    Возвращаем статус каждого компонента + общий статус.
    """
    checks = {}
    all_ok = True

    # проверка БД — простой select 1
    try:
        async with async_session() as session:
            await session.execute(text("select 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
        all_ok = False

    # проверка Redis — пингуем
    try:
        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(settings.REDIS_URL)
        pong = await redis_client.ping()
        await redis_client.aclose()
        checks["redis"] = {"status": "ok" if pong else "error"}
        if not pong:
            all_ok = False
    except Exception as e:
        checks["redis"] = {"status": "error", "detail": str(e)}
        all_ok = False

    # проверка Telegram-бота — просто проверяем что токен задан
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "":
        checks["telegram"] = {"status": "ok", "detail": "Токен настроен"}
    else:
        checks["telegram"] = {"status": "warning", "detail": "Токен не настроен"}

    # проверка AI-провайдера — проверяем что хоть один API-ключ задан
    ai_configured = False
    ai_providers = []

    if settings.ANTHROPIC_API_KEY:
        ai_configured = True
        ai_providers.append("anthropic")
    if settings.OPENAI_API_KEY:
        ai_configured = True
        ai_providers.append("openai")

    if ai_configured:
        checks["ai_provider"] = {
            "status": "ok",
            "detail": f"Настроены: {', '.join(ai_providers)}",
        }
    else:
        checks["ai_provider"] = {
            "status": "warning",
            "detail": "Ни один AI-провайдер не настроен",
        }

    return {
        "status": "ok" if all_ok else "degraded",
        "version": "0.1.0",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }
