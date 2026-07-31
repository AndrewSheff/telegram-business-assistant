"""
Роутер аутентификации — логин и смена пароля.
Рейт-лимит на логин, чтоб не брутфорсили.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.core.security import create_access_token, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Логин по email + пароль — возвращаем JWT-токен.
    OAuth2-форма: username = email, password = пароль.
    Лимит 5 попыток в минуту, чтоб боты не лезли.
    """
    user_response, must_change_password = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password,
        db=db,
    )

    # Генерим токен — кладем user_id, email, имя, роль и флаг смены пароля
    access_token = create_access_token(data={
        "sub": str(user_response.id),
        "email": user_response.email,
        "name": user_response.name,
        "role": user_response.role.value if hasattr(user_response.role, 'value') else user_response.role,
        "must_change_password": must_change_password,
    })

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Смена пароля — нужен текущий пароль + новый с подтверждением.
    Валидация (совпадение, длина) уже в схеме, тут только бизнес-логика.
    """
    await auth_service.change_password(
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
        db=db,
    )

    return {"detail": "Пароль успешно изменен"}
