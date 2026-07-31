"""
Тесты рассылок — список, создание, отправка, удаление.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from app.core.exceptions import AppError
from app.schemas.broadcast import BroadcastListResponse, BroadcastResponse


def _make_broadcast_response(broadcast_id=None, status="draft", title="Акция"):
    """Собираем BroadcastResponse для моков"""
    return BroadcastResponse(
        id=broadcast_id or uuid.uuid4(),
        title=title,
        content="Скидка 20% на все услуги!",
        image_url=None,
        segment="all",
        segment_days=None,
        status=status,
        total_count=0,
        sent_count=0,
        failed_count=0,
        scheduled_at=None,
        completed_at=None,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


async def test_list_broadcasts(owner_client):
    """Список рассылок"""
    client, headers = owner_client
    mock_response = BroadcastListResponse(
        items=[_make_broadcast_response(), _make_broadcast_response(title="Праздник")],
        total=2,
        page=1,
        size=20,
    )

    with patch(
        "app.api.v1.broadcasts.broadcast_service.list_broadcasts", new_callable=AsyncMock
    ) as mock_list:
        mock_list.return_value = mock_response

        response = await client.get("/api/v1/broadcasts", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


async def test_create_broadcast(owner_client):
    """Создание рассылки"""
    client, headers = owner_client
    new_broadcast = _make_broadcast_response(title="Новогодняя акция")

    with patch(
        "app.api.v1.broadcasts.broadcast_service.create_broadcast", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = new_broadcast

        response = await client.post(
            "/api/v1/broadcasts",
            json={
                "title": "Новогодняя акция",
                "content": "Скидка 20% на все услуги!",
                "segment": "all",
            },
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Новогодняя акция"
    assert data["status"] == "draft"


async def test_send_broadcast(owner_client):
    """Запуск отправки рассылки"""
    client, headers = owner_client
    broadcast_id = uuid.uuid4()
    sending_broadcast = _make_broadcast_response(broadcast_id=broadcast_id, status="sending")
    sending_broadcast.total_count = 42

    with patch(
        "app.api.v1.broadcasts.broadcast_service.start_send", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = sending_broadcast

        response = await client.post(
            f"/api/v1/broadcasts/{broadcast_id}/send",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sending"


async def test_delete_draft_broadcast(owner_client):
    """Удаление черновика рассылки — 204"""
    client, headers = owner_client
    broadcast_id = uuid.uuid4()

    with patch(
        "app.api.v1.broadcasts.broadcast_service.delete_broadcast", new_callable=AsyncMock
    ) as mock_delete:
        mock_delete.return_value = None

        response = await client.delete(
            f"/api/v1/broadcasts/{broadcast_id}",
            headers=headers,
        )

    assert response.status_code == 204


async def test_delete_non_draft_broadcast(owner_client):
    """Удаление отправленной рассылки — 400 (нельзя удалять не-черновик)"""
    client, headers = owner_client
    broadcast_id = uuid.uuid4()

    with patch(
        "app.api.v1.broadcasts.broadcast_service.delete_broadcast", new_callable=AsyncMock
    ) as mock_delete:
        mock_delete.side_effect = AppError(
            status_code=400,
            detail="Удалить можно только черновик рассылки",
        )

        response = await client.delete(
            f"/api/v1/broadcasts/{broadcast_id}",
            headers=headers,
        )

    assert response.status_code == 400
    assert "черновик" in response.json()["detail"]
