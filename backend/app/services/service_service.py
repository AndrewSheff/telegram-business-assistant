"""
Сервис для работы с услугами и категориями.
Тут вся бизнес-логика: CRUD, сортировка, проверка зависимостей.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.booking import Booking
from app.models.service import Service
from app.models.service_category import ServiceCategory
from app.schemas.service import (
    CategoryCreate,
    CategoryUpdate,
    ServiceCreate,
    ServiceUpdate,
)


async def list_services(
    db: AsyncSession,
    include_inactive: bool = False,
) -> list[Service]:
    """
    Получаем все услуги, сортируем по sort_order.
    Если include_inactive=False, то только активные — логично же.
    """
    query = select(Service).order_by(Service.sort_order, Service.name)
    if not include_inactive:
        query = query.where(Service.is_active.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_service(service_id: uuid.UUID, db: AsyncSession) -> Service:
    """Ищем услугу по id — если нет, кидаем 404."""
    result = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise NotFoundError(f"Услуга с id {service_id} не найдена")
    return service


async def create_service(data: ServiceCreate, db: AsyncSession) -> Service:
    """
    Создаем новую услугу.
    Если указана категория — проверяем что она существует.
    """
    if data.category_id is not None:
        category = await db.execute(
            select(ServiceCategory).where(ServiceCategory.id == data.category_id)
        )
        if category.scalar_one_or_none() is None:
            raise NotFoundError(f"Категория с id {data.category_id} не найдена")

    service = Service(
        name=data.name,
        description=data.description,
        price=data.price,
        duration_minutes=data.duration_minutes,
        category_id=data.category_id,
        sort_order=data.sort_order or 0,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    db: AsyncSession,
) -> Service:
    """
    Обновляем услугу — меняем только то, что пришло (не None).
    Категорию тоже проверяем на существование.
    """
    service = await get_service(service_id, db)

    update_data = data.model_dump(exclude_unset=True)

    # Если меняют категорию — проверим что она есть
    if "category_id" in update_data and update_data["category_id"] is not None:
        category = await db.execute(
            select(ServiceCategory).where(
                ServiceCategory.id == update_data["category_id"]
            )
        )
        if category.scalar_one_or_none() is None:
            raise NotFoundError(
                f"Категория с id {update_data['category_id']} не найдена"
            )

    for field, value in update_data.items():
        setattr(service, field, value)

    await db.commit()
    await db.refresh(service)
    return service


async def delete_service(service_id: uuid.UUID, db: AsyncSession) -> None:
    """
    Удаляем услугу — но сначала проверим, нет ли активных записей.
    Если есть pending/confirmed бронирования — не дадим удалить.
    """
    service = await get_service(service_id, db)

    # Проверяем активные бронирования (pending или confirmed)
    active_bookings = await db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.service_id == service_id,
            Booking.status.in_(["pending", "confirmed"]),
        )
    )
    count = active_bookings.scalar()
    if count and count > 0:
        raise ConflictError(
            f"Нельзя удалить услугу — есть {count} активных бронирований"
        )

    await db.delete(service)
    await db.commit()


async def list_categories(db: AsyncSession) -> list[ServiceCategory]:
    """Список всех категорий, сортированный по sort_order — просто и понятно."""
    result = await db.execute(
        select(ServiceCategory).order_by(ServiceCategory.sort_order, ServiceCategory.name)
    )
    return list(result.scalars().all())


async def create_category(
    data: CategoryCreate,
    db: AsyncSession,
) -> ServiceCategory:
    """Создаем категорию — ничего сложного, название + порядок."""
    category = ServiceCategory(
        name=data.name,
        sort_order=data.sort_order or 0,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: AsyncSession,
) -> ServiceCategory:
    """Обновляем категорию — только пришедшие поля."""
    result = await db.execute(
        select(ServiceCategory).where(ServiceCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise NotFoundError(f"Категория с id {category_id} не найдена")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(category_id: uuid.UUID, db: AsyncSession) -> None:
    """
    Удаляем категорию — но если в ней есть услуги, не дадим.
    Сначала перенеси или удали услуги, потом уже категорию.
    """
    result = await db.execute(
        select(ServiceCategory).where(ServiceCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise NotFoundError(f"Категория с id {category_id} не найдена")

    # Проверяем, есть ли услуги в этой категории
    services_count = await db.execute(
        select(func.count()).select_from(Service).where(
            Service.category_id == category_id
        )
    )
    count = services_count.scalar()
    if count and count > 0:
        raise ConflictError(
            f"Нельзя удалить категорию — в ней {count} услуг. "
            "Сначала перенеси или удали их"
        )

    await db.delete(category)
    await db.commit()
