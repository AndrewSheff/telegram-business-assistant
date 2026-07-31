"""
Роутер пользователей — CRUD для владельца + профиль для всех.
Owner рулит командой, остальные могут только свой профиль менять.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


# --- Эндпоинты профиля идут первыми, иначе /me матчится как /{user_id} ---


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Инфа о текущем юзере — доступно всем авторизованным."""
    return UserResponse.model_validate(current_user)


@router.put("/me/profile", response_model=UserResponse)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновляем свой профиль — пока только имя можно менять."""
    return await user_service.update_profile(current_user, data.name, db)


# --- CRUD для владельца — управление командой ---


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Список всех юзеров — только для владельца."""
    return await user_service.list_users(db)


@router.post("", response_model=dict)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """
    Создаем нового юзера — возвращаем его данные + временный пароль.
    Пароль показывается один раз, потом юзер сменит его при входе.
    """
    user_response, temp_password = await user_service.create_user(data, db)

    return {
        "user": user_response.model_dump(mode="json"),
        "temp_password": temp_password,
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Обновляем юзера — имя, email, роль, активность. Только для владельца."""
    return await user_service.update_user(str(user_id), data, db)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Удаляем юзера — нельзя удалить самого себя. Только для владельца."""
    await user_service.delete_user(str(user_id), current_user, db)
    return {"detail": "Пользователь удален"}
