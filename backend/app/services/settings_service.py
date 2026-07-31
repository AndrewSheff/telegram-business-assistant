"""
Сервис настроек бизнеса — получение и обновление конфига.
Настройки — синглтон, всегда одна запись в таблице.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_settings import BusinessSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate

logger = structlog.get_logger(__name__)


async def get_settings(db: AsyncSession) -> SettingsResponse:
    """
    Получаем настройки бизнеса — если их нет, создаем дефолтные.
    Всегда возвращаем ровно одну запись, не больше.
    """
    result = await db.execute(select(BusinessSettings))
    settings = result.scalar_one_or_none()

    if settings is None:
        # Первый запуск — создаем пустые настройки
        settings = BusinessSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        logger.info("default_settings_created")

    return _to_response(settings)


async def update_settings(data: SettingsUpdate, db: AsyncSession) -> SettingsResponse:
    """
    Обновляем настройки — меняем только переданные поля.
    Если настроек еще нет — создаем и сразу обновляем.
    """
    result = await db.execute(select(BusinessSettings))
    settings = result.scalar_one_or_none()

    if settings is None:
        settings = BusinessSettings()
        db.add(settings)

    # Обновляем только то что прислали
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    logger.info("settings_updated", fields=list(update_data.keys()))

    return _to_response(settings)


def _to_response(settings: BusinessSettings) -> SettingsResponse:
    """
    Конвертим модель в ответ — бот-токен не отдаем,
    только флаг что он установлен (безопасность, все дела).
    """
    return SettingsResponse(
        id=settings.id,
        bot_token_set=settings.bot_token is not None and len(settings.bot_token) > 0,
        business_name=settings.business_name,
        description=settings.description,
        address=settings.address,
        phone=settings.phone,
        website=settings.website,
        welcome_message=settings.welcome_message,
        offline_message=settings.offline_message,
        timezone=settings.timezone,
        min_cancel_hours=settings.min_cancel_hours,
        ai_model=settings.ai_model,
        ai_system_prompt=settings.ai_system_prompt,
        updated_at=settings.updated_at,
    )
