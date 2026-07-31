"""
Сервис управления пользователями — CRUD, профиль, генерация временных паролей.
Все манипуляции с юзерами проходят через этот сервис.
"""

import secrets
import string

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

logger = structlog.get_logger(__name__)

# Алфавит для генерации временного пароля — буквы и цифры, без путаницы
TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits
TEMP_PASSWORD_LENGTH = 12


def generate_temp_password() -> str:
    """Генерим рандомный временный пароль — 12 символов, буквы + цифры."""
    return "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(TEMP_PASSWORD_LENGTH))


async def list_users(db: AsyncSession) -> list[UserResponse]:
    """Список всех юзеров — для панели управления владельца."""
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


async def get_user(user_id: str, db: AsyncSession) -> UserResponse:
    """Получаем юзера по ID — если нет, кидаем 404."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundError(detail="Пользователь не найден")

    return UserResponse.model_validate(user)


async def create_user(data: UserCreate, db: AsyncSession) -> tuple[UserResponse, str]:
    """
    Создаем нового юзера с временным паролем.
    Возвращаем юзера + пароль, чтобы можно было показать владельцу.
    """
    # Проверяем уникальность email
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(detail="Пользователь с таким email уже существует")

    temp_password = generate_temp_password()

    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(temp_password),
        role=data.role.value,
        is_active=True,
        must_change_password=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_created", user_id=str(user.id), email=user.email, role=user.role)

    return UserResponse.model_validate(user), temp_password


async def update_user(user_id: str, data: UserUpdate, db: AsyncSession) -> UserResponse:
    """
    Обновляем юзера — имя, email, роль, активность.
    Нельзя забрать у владельца роль owner, если он единственный.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundError(detail="Пользователь не найден")

    # Проверяем уникальность email если меняем
    if data.email is not None and data.email != user.email:
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(detail="Пользователь с таким email уже существует")

    # Обновляем только переданные поля
    update_data = data.model_dump(exclude_unset=True)
    if "role" in update_data:
        update_data["role"] = update_data["role"].value if update_data["role"] else update_data["role"]

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    logger.info("user_updated", user_id=str(user.id))

    return UserResponse.model_validate(user)


async def delete_user(user_id: str, current_user: User, db: AsyncSession) -> None:
    """
    Удаляем юзера — нельзя удалить самого себя, это было бы странно.
    """
    if str(current_user.id) == str(user_id):
        raise ForbiddenError(detail="Нельзя удалить самого себя")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundError(detail="Пользователь не найден")

    # Нельзя удалить единственного owner — система останется без управления
    if user.role == "owner":
        from sqlalchemy import func
        owner_count_result = await db.execute(
            select(func.count()).select_from(User).where(User.role == "owner")
        )
        owner_count = owner_count_result.scalar() or 0
        if owner_count <= 1:
            raise ForbiddenError(detail="Нельзя удалить единственного владельца")

    await db.delete(user)
    await db.commit()

    logger.info("user_deleted", user_id=str(user_id), deleted_by=str(current_user.id))


async def update_profile(user: User, name: str, db: AsyncSession) -> UserResponse:
    """Обновляем профиль текущего юзера — пока только имя можно менять."""
    user.name = name

    await db.commit()
    await db.refresh(user)

    logger.info("profile_updated", user_id=str(user.id))

    return UserResponse.model_validate(user)
