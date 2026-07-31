"""
Роутер настроек бизнеса — получение и обновление.
Только для владельца — тут токен бота и всякое чувствительное.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.database import get_db
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Получаем настройки бизнеса — бот-токен скрыт, только флаг наличия."""
    return await settings_service.get_settings(db)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Обновляем настройки бизнеса — меняем только переданные поля."""
    return await settings_service.update_settings(data, db)
