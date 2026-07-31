"""
API для дашборда — статистика, графики активности, топ услуг и вопросов.
Все эндпоинты требуют авторизации (owner или operator).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.schemas.dashboard import ActivityPoint, DashboardStats, TopQuestion, TopService
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Дашборд"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Основная статистика для карточек на главной."""
    return await dashboard_service.get_stats(db)


@router.get("/activity", response_model=list[ActivityPoint])
async def get_activity(
    days: int = Query(30, ge=1, le=365, description="Количество дней для графика"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """График активности за последние N дней — бронирования и взаимодействия."""
    return await dashboard_service.get_activity(db, days=days)


@router.get("/top-services", response_model=list[TopService])
async def get_top_services(
    limit: int = Query(5, ge=1, le=20, description="Количество услуг в рейтинге"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Топ самых популярных услуг по количеству бронирований."""
    return await dashboard_service.get_top_services(db, limit=limit)


@router.get("/top-questions", response_model=list[TopQuestion])
async def get_top_questions(
    limit: int = Query(5, ge=1, le=20, description="Количество вопросов в рейтинге"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Топ самых частых вопросов от клиентов."""
    return await dashboard_service.get_top_questions(db, limit=limit)
