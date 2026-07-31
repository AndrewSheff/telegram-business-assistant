"""
Тесты аутентификации — логин, смена пароля, проверка токенов.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from app.core.exceptions import ForbiddenError
from app.schemas.user import UserResponse

# -- Тестовые данные --

MOCK_USER_RESPONSE = UserResponse(
    id=uuid.uuid4(),
    email="test@example.com",
    name="Test User",
    role="owner",
    is_active=True,
    must_change_password=False,
    created_at=datetime(2025, 1, 1, tzinfo=UTC),
)


async def test_login_success(client):
    """Успешный логин — мокаем auth_service.authenticate, ждем JWT в ответе"""
    with patch("app.services.auth_service.authenticate", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = (MOCK_USER_RESPONSE, False)

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "correctpassword"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"


async def test_login_invalid_credentials(client):
    """Неверные данные — сервис кидает ForbiddenError, ждем 403"""
    with patch("app.services.auth_service.authenticate", new_callable=AsyncMock) as mock_auth:
        mock_auth.side_effect = ForbiddenError(detail="Неверный email или пароль")

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "wrong@email.com", "password": "wrongpassword"},
        )

    assert response.status_code == 403
    assert "Неверный" in response.json()["detail"]


async def test_login_inactive_user(client):
    """Заблокированный аккаунт — тоже 403"""
    with patch("app.services.auth_service.authenticate", new_callable=AsyncMock) as mock_auth:
        mock_auth.side_effect = ForbiddenError(detail="Аккаунт деактивирован")

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "blocked@example.com", "password": "somepassword"},
        )

    assert response.status_code == 403
    assert "деактивирован" in response.json()["detail"]


async def test_change_password_success(owner_client):
    """Успешная смена пароля"""
    client, headers = owner_client

    with patch("app.services.auth_service.change_password", new_callable=AsyncMock) as mock_change:
        mock_change.return_value = None

        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPass123",
                "new_password": "NewPass123",
                "confirm_password": "NewPass123",
            },
            headers=headers,
        )

    assert response.status_code == 200
    assert "успешно" in response.json()["detail"]


async def test_change_password_wrong_current(owner_client):
    """Неверный текущий пароль — сервис кидает ForbiddenError"""
    client, headers = owner_client

    with patch("app.services.auth_service.change_password", new_callable=AsyncMock) as mock_change:
        mock_change.side_effect = ForbiddenError(detail="Текущий пароль неверный")

        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongOldPass",
                "new_password": "NewPass123",
                "confirm_password": "NewPass123",
            },
            headers=headers,
        )

    assert response.status_code == 403


async def test_change_password_unauthenticated(client):
    """Смена пароля без токена — 401"""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "OldPass123",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123",
        },
    )

    assert response.status_code == 401
