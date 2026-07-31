"""
Сервис аутентификации — логин, смена пароля, создание начального админа.
Все что связано с входом в систему живет тут.
"""

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserResponse

logger = structlog.get_logger(__name__)


async def authenticate(email: str, password: str, db: AsyncSession) -> tuple[UserResponse, bool]:
    """
    Проверяем логин/пароль и возвращаем юзера + флаг must_change_password.
    Если что-то не так — кидаем ошибку, тут без компромиссов.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError(detail="Неверный email или пароль")

    if not user.is_active:
        raise ForbiddenError(detail="Аккаунт деактивирован")

    logger.info("user_authenticated", user_id=str(user.id), email=user.email)

    return UserResponse.model_validate(user), user.must_change_password


async def change_password(
    user: User,
    current_password: str,
    new_password: str,
    db: AsyncSession,
) -> None:
    """
    Смена пароля — проверяем старый, ставим новый, снимаем флаг must_change_password.
    Ничего космического, но без этого никуда.
    """
    if not verify_password(current_password, user.password_hash):
        raise ForbiddenError(detail="Текущий пароль неверный")

    user.password_hash = hash_password(new_password)
    user.must_change_password = False

    await db.commit()
    await db.refresh(user)

    logger.info("password_changed", user_id=str(user.id))


async def create_initial_admin(db: AsyncSession) -> None:
    """
    Создаем владельца при первом запуске, если в базе пусто.
    Берем данные из конфига — email, имя, дефолтный пароль.
    """
    result = await db.execute(select(func.count()).select_from(User))
    user_count = result.scalar()

    if user_count > 0:
        logger.info("initial_admin_skip", reason="users already exist")
        return

    admin = User(
        email=settings.ADMIN_EMAIL,
        name=settings.ADMIN_NAME,
        password_hash=hash_password(settings.ADMIN_DEFAULT_PASSWORD),
        role="owner",
        is_active=True,
        must_change_password=True,
    )

    db.add(admin)
    await db.commit()

    logger.info(
        "initial_admin_created",
        email=settings.ADMIN_EMAIL,
        name=settings.ADMIN_NAME,
    )
