"""
Роутер для управления услугами и категориями.
CRUD-операции, доступ: чтение — все авторизованные, запись — только owner.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.schemas.service import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.services import service_service

router = APIRouter(prefix="/api/v1/services", tags=["services"])


# --- Категории (идут ПЕРЕД /{service_id}, чтобы не перехватывал) ---


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Список категорий услуг — доступно всем авторизованным."""
    return await service_service.list_categories(db)


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Создать категорию — только для owner."""
    return await service_service.create_category(data, db)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Обновить категорию — только для owner."""
    return await service_service.update_category(category_id, data, db)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Удалить категорию — только если в ней нет услуг."""
    await service_service.delete_category(category_id, db)


# --- Услуги ---


@router.get("", response_model=list[ServiceResponse])
async def get_services(
    include_inactive: bool = Query(False, description="Показывать неактивные услуги"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """
    Список услуг — по умолчанию только активные.
    Если include_inactive=true, вернем все вместе с выключенными.
    """
    services = await service_service.list_services(db, include_inactive=include_inactive)

    # Собираем ответ с названием категории
    result = []
    for s in services:
        response = ServiceResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            price=s.price,
            duration_minutes=s.duration_minutes,
            category_id=s.category_id,
            category_name=s.category.name if s.category else None,
            sort_order=s.sort_order,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        result.append(response)
    return result


@router.post("", response_model=ServiceResponse, status_code=201)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Создать услугу — только для owner."""
    service = await service_service.create_service(data, db)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        price=service.price,
        duration_minutes=service.duration_minutes,
        category_id=service.category_id,
        category_name=service.category.name if service.category else None,
        sort_order=service.sort_order,
        is_active=service.is_active,
        created_at=service.created_at,
    )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Получить конкретную услугу по id."""
    service = await service_service.get_service(service_id, db)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        price=service.price,
        duration_minutes=service.duration_minutes,
        category_id=service.category_id,
        category_name=service.category.name if service.category else None,
        sort_order=service.sort_order,
        is_active=service.is_active,
        created_at=service.created_at,
    )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Обновить услугу — только для owner."""
    service = await service_service.update_service(service_id, data, db)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        price=service.price,
        duration_minutes=service.duration_minutes,
        category_id=service.category_id,
        category_name=service.category.name if service.category else None,
        sort_order=service.sort_order,
        is_active=service.is_active,
        created_at=service.created_at,
    )


@router.delete("/{service_id}", status_code=204)
async def delete_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("owner")),
):
    """Удалить услугу — только если нет активных бронирований."""
    await service_service.delete_service(service_id, db)
