"""
Тесты бронирований — список, фильтры, статусы, конфликты.
"""

import uuid
from datetime import UTC, date, datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ConflictError, NotFoundError


def _make_booking_mock(
    booking_id=None,
    status="pending",
    booking_date=None,
    start_time_val=None,
    end_time_val=None,
):
    """Мок бронирования с клиентом и услугой"""
    b = MagicMock()
    b.id = booking_id or uuid.uuid4()
    b.client_id = uuid.uuid4()
    b.service_id = uuid.uuid4()
    b.booking_date = booking_date or date(2025, 3, 15)
    b.start_time = start_time_val or time(10, 0)
    b.end_time = end_time_val or time(11, 0)
    b.status = status
    b.notes = None
    b.created_at = datetime(2025, 1, 1, tzinfo=UTC)

    # реляшены
    b.client = MagicMock()
    b.client.first_name = "Иван"
    b.service = MagicMock()
    b.service.name = "Стрижка"

    return b


async def test_list_bookings(owner_client):
    """Список бронирований с пагинацией"""
    client, headers = owner_client
    mock_bookings = [_make_booking_mock(), _make_booking_mock(status="confirmed")]

    with patch(
        "app.api.v1.bookings.booking_service.list_bookings", new_callable=AsyncMock
    ) as mock_list:
        mock_list.return_value = (mock_bookings, 2)

        response = await client.get("/api/v1/bookings", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


async def test_get_today_bookings(owner_client):
    """Бронирования на сегодня"""
    client, headers = owner_client
    today_bookings = [_make_booking_mock(booking_date=date.today())]

    with patch(
        "app.api.v1.bookings.booking_service.get_today_bookings", new_callable=AsyncMock
    ) as mock_today:
        mock_today.return_value = today_bookings

        response = await client.get("/api/v1/bookings/today", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


async def test_update_booking_status_confirm(owner_client):
    """Подтверждение бронирования — pending -> confirmed"""
    client, headers = owner_client
    booking_id = uuid.uuid4()
    confirmed_booking = _make_booking_mock(booking_id=booking_id, status="confirmed")

    with patch(
        "app.api.v1.bookings.booking_service.update_booking_status", new_callable=AsyncMock
    ) as mock_update:
        mock_update.return_value = confirmed_booking

        response = await client.patch(
            f"/api/v1/bookings/{booking_id}/status",
            json={"status": "confirmed"},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


async def test_update_booking_status_invalid_transition(owner_client):
    """Недопустимый переход статуса — 409"""
    client, headers = owner_client
    booking_id = uuid.uuid4()

    with patch(
        "app.api.v1.bookings.booking_service.update_booking_status", new_callable=AsyncMock
    ) as mock_update:
        mock_update.side_effect = ConflictError(
            "Нельзя сменить статус с 'completed' на 'pending'"
        )

        response = await client.patch(
            f"/api/v1/bookings/{booking_id}/status",
            json={"status": "pending"},
            headers=headers,
        )

    assert response.status_code == 409


async def test_create_booking_conflict(owner_client):
    """Попытка забронировать занятый слот — 409"""
    client, headers = owner_client
    booking_id = uuid.uuid4()

    with patch(
        "app.api.v1.bookings.booking_service.update_booking_status", new_callable=AsyncMock
    ) as mock_update:
        mock_update.side_effect = ConflictError("Этот слот уже занят")

        response = await client.patch(
            f"/api/v1/bookings/{booking_id}/status",
            json={"status": "confirmed"},
            headers=headers,
        )

    assert response.status_code == 409
    assert "занят" in response.json()["detail"]


async def test_get_booking_not_found(owner_client):
    """Бронирование не найдено — 404"""
    client, headers = owner_client
    fake_id = uuid.uuid4()

    with patch(
        "app.api.v1.bookings.booking_service.get_booking", new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = NotFoundError("Бронирование не найдено")

        response = await client.get(
            f"/api/v1/bookings/{fake_id}",
            headers=headers,
        )

    # NotFoundError кидает HTTPException с 404
    assert response.status_code == 404
