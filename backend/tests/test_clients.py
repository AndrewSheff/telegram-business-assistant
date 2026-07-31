"""
Тесты клиентов — список с поиском, детали, обновление заметок, история.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from app.schemas.client import ClientListResponse, ClientResponse


def _make_client_response(client_id=None, first_name="Иван"):
    """Собираем ClientResponse для моков"""
    return ClientResponse(
        id=client_id or uuid.uuid4(),
        telegram_id=123456789,
        first_name=first_name,
        last_name="Петров",
        username="ivan_p",
        phone=None,
        notes=None,
        is_blocked=False,
        last_interaction_at=datetime(2025, 3, 1, tzinfo=UTC),
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        bookings_count=5,
    )


async def test_list_clients_with_search(owner_client):
    """Список клиентов с поиском"""
    client, headers = owner_client
    mock_response = ClientListResponse(
        items=[_make_client_response(first_name="Иван"), _make_client_response(first_name="Ивана")],
        total=2,
        page=1,
        size=20,
    )

    with patch("app.api.v1.clients.client_service.list_clients", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_response

        response = await client.get(
            "/api/v1/clients?search=Иван",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


async def test_get_client(owner_client):
    """Получение одного клиента"""
    client, headers = owner_client
    client_id = uuid.uuid4()
    mock_client = _make_client_response(client_id=client_id, first_name="Мария")

    with patch("app.api.v1.clients.client_service.get_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_client

        response = await client.get(
            f"/api/v1/clients/{client_id}",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Мария"


async def test_update_client_notes(owner_client):
    """Обновление заметок клиента"""
    client, headers = owner_client
    client_id = uuid.uuid4()
    updated_client = _make_client_response(client_id=client_id)
    updated_client.notes = "VIP-клиент, всегда записывается на 15:00"

    with patch("app.api.v1.clients.client_service.update_client", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = updated_client

        response = await client.patch(
            f"/api/v1/clients/{client_id}",
            json={"notes": "VIP-клиент, всегда записывается на 15:00"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "VIP" in data["notes"]


async def test_get_client_history(owner_client):
    """История клиента — бронирования и сообщения"""
    client, headers = owner_client
    client_id = uuid.uuid4()

    mock_history = {
        "bookings": [],
        "messages": [],
    }

    with patch(
        "app.api.v1.clients.client_service.get_client_history", new_callable=AsyncMock
    ) as mock_hist:
        mock_hist.return_value = mock_history

        response = await client.get(
            f"/api/v1/clients/{client_id}/history",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "bookings" in data
    assert "messages" in data
