"""
Общие фикстуры для тестов — мокаем БД, создаем клиента, готовим токены.
Никаких реальных баз данных тут не будет, все на моках.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.security import OAuth2PasswordRequestForm
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user
from app.database import get_db
from app.schemas.auth import ChangePasswordRequest, LoginResponse
from app.services import auth_service

# -- Тестовые данные --

OWNER_ID = uuid.uuid4()
OPERATOR_ID = uuid.uuid4()


def _make_mock_user(user_id: uuid.UUID, role: str, email: str, name: str) -> MagicMock:
    """Хелпер — создает мок юзера с нужными полями"""
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.name = name
    user.role = role
    user.is_active = True
    user.must_change_password = False
    user.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    user.password_hash = "fake_hash"
    return user


MOCK_OWNER = _make_mock_user(OWNER_ID, "owner", "owner@test.com", "Test Owner")
MOCK_OPERATOR = _make_mock_user(OPERATOR_ID, "operator", "operator@test.com", "Test Operator")


# -- Фикстуры для БД --


@pytest.fixture()
def mock_db():
    """Мок сессии БД — ничего не делает, зато быстро"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    return session


# -- Фикстуры для токенов --


@pytest.fixture()
def owner_token() -> str:
    """JWT-токен для owner"""
    return create_access_token(data={"sub": str(OWNER_ID)})


@pytest.fixture()
def operator_token() -> str:
    """JWT-токен для operator"""
    return create_access_token(data={"sub": str(OPERATOR_ID)})


@pytest.fixture()
def owner_headers(owner_token: str) -> dict:
    """Заголовки авторизации для owner"""
    return {"Authorization": f"Bearer {owner_token}"}


@pytest.fixture()
def operator_headers(operator_token: str) -> dict:
    """Заголовки авторизации для operator"""
    return {"Authorization": f"Bearer {operator_token}"}


# -- Auth-роутер без rate_limit (для тестов) --


def _make_test_auth_router():
    """
    Создаем auth-роутер без декоратора @limiter.limit —
    чтоб в тестах не было попыток подключиться к Redis.
    """
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/login", response_model=LoginResponse)
    async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
    ):
        user_response, must_change_password = await auth_service.authenticate(
            email=form_data.username, password=form_data.password, db=db,
        )
        access_token = create_access_token(data={"sub": str(user_response.id)})
        return LoginResponse(access_token=access_token, token_type="bearer", user=user_response)

    @router.post("/change-password")
    async def change_password(
        data: ChangePasswordRequest,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        await auth_service.change_password(
            user=current_user, current_password=data.current_password,
            new_password=data.new_password, db=db,
        )
        return {"detail": "Пароль успешно изменен"}

    return router


# -- Хелпер для создания тестового приложения --


def _create_test_app(mock_db_session, mock_user=None):
    """
    Создаем тестовое FastAPI-приложение с заглушенными зависимостями.
    Каждый раз новое, чтоб тесты не мешали друг другу.
    """

    @asynccontextmanager
    async def _noop_lifespan(app: FastAPI):
        yield

    test_app = FastAPI(lifespan=_noop_lifespan)

    # Подключаем все роутеры, auth — без rate_limit
    from app.api.v1.bookings import router as bookings_router
    from app.api.v1.broadcasts import router as broadcasts_router
    from app.api.v1.clients import router as clients_router
    from app.api.v1.dashboard import router as dashboard_router
    from app.api.v1.faq import router as faq_router
    from app.api.v1.schedule import router as schedule_router
    from app.api.v1.services_mgmt import router as services_router

    test_app.include_router(_make_test_auth_router(), prefix="/api/v1")
    test_app.include_router(services_router)
    test_app.include_router(schedule_router)
    test_app.include_router(bookings_router)
    test_app.include_router(clients_router, prefix="/api/v1")
    test_app.include_router(faq_router, prefix="/api/v1")
    test_app.include_router(broadcasts_router, prefix="/api/v1")
    test_app.include_router(dashboard_router, prefix="/api/v1")

    # Подменяем зависимости
    async def _override_get_db():
        yield mock_db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    if mock_user is not None:
        test_app.dependency_overrides[get_current_user] = lambda: mock_user

    return test_app


# -- Главные фикстуры: клиенты для разных ролей --


@pytest.fixture()
async def client(mock_db):
    """
    HTTP-клиент БЕЗ авторизации — для тестов логина и проверки 401.
    """
    test_app = _create_test_app(mock_db)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def owner_client(mock_db):
    """Клиент с авторизацией owner — get_current_user возвращает мок owner-а"""
    test_app = _create_test_app(mock_db, mock_user=MOCK_OWNER)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, {"Authorization": "Bearer fake-owner-token"}


@pytest.fixture()
async def operator_client(mock_db):
    """Клиент с авторизацией operator — get_current_user возвращает мок operator-а"""
    test_app = _create_test_app(mock_db, mock_user=MOCK_OPERATOR)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, {"Authorization": "Bearer fake-operator-token"}
