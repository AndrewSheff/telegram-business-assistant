"""
Тесты для управления услугами — CRUD, проверка ролей.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ConflictError

# -- Тестовые данные --


def _make_service_mock(
    service_id=None, name="Стрижка", price=1500, duration=60, is_active=True
):
    """Мок услуги с реляшенами"""
    svc = MagicMock()
    svc.id = service_id or uuid.uuid4()
    svc.name = name
    svc.description = "Классная стрижка"
    svc.price = Decimal(str(price))
    svc.duration_minutes = duration
    svc.category_id = uuid.uuid4()
    svc.category = MagicMock()
    svc.category.name = "Парикмахерская"
    svc.sort_order = 0
    svc.is_active = is_active
    svc.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    return svc


async def test_list_services(owner_client):
    """Получение списка услуг"""
    client, headers = owner_client
    mock_services = [_make_service_mock(), _make_service_mock(name="Маникюр", price=1000)]

    with patch("app.api.v1.services_mgmt.service_service.list_services", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_services

        response = await client.get("/api/v1/services", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Стрижка"
    assert data[1]["name"] == "Маникюр"


async def test_create_service(owner_client):
    """Создание услуги — только owner"""
    client, headers = owner_client
    new_service = _make_service_mock(name="Покраска", price=3000)

    with patch("app.api.v1.services_mgmt.service_service.create_service", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = new_service

        response = await client.post(
            "/api/v1/services",
            json={
                "name": "Покраска",
                "price": 3000,
                "duration_minutes": 90,
            },
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Покраска"


async def test_create_service_unauthorized(operator_client):
    """Оператор не может создавать услуги — 403"""
    client, headers = operator_client

    response = await client.post(
        "/api/v1/services",
        json={
            "name": "Запрещенная услуга",
            "price": 999,
            "duration_minutes": 30,
        },
        headers=headers,
    )

    assert response.status_code == 403


async def test_update_service(owner_client):
    """Обновление услуги"""
    client, headers = owner_client
    service_id = uuid.uuid4()
    updated_service = _make_service_mock(service_id=service_id, name="Стрижка VIP", price=2000)

    with patch("app.api.v1.services_mgmt.service_service.update_service", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = updated_service

        response = await client.put(
            f"/api/v1/services/{service_id}",
            json={"name": "Стрижка VIP", "price": 2000},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Стрижка VIP"


async def test_delete_service(owner_client):
    """Удаление услуги — 204 No Content"""
    client, headers = owner_client
    service_id = uuid.uuid4()

    with patch("app.api.v1.services_mgmt.service_service.delete_service", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = None

        response = await client.delete(
            f"/api/v1/services/{service_id}",
            headers=headers,
        )

    assert response.status_code == 204


async def test_delete_service_with_bookings(owner_client):
    """Удаление услуги с активными бронированиями — 409"""
    client, headers = owner_client
    service_id = uuid.uuid4()

    with patch("app.api.v1.services_mgmt.service_service.delete_service", new_callable=AsyncMock) as mock_delete:
        mock_delete.side_effect = ConflictError(
            "Нельзя удалить услугу — есть 3 активных бронирований"
        )

        response = await client.delete(
            f"/api/v1/services/{service_id}",
            headers=headers,
        )

    assert response.status_code == 409
    assert "активных" in response.json()["detail"]
