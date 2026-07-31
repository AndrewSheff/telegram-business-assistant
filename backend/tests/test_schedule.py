"""
Тесты расписания — рабочие часы, исключения, свободные слоты.
"""

import uuid
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.schedule import TimeSlot


def _make_working_hours_mock(day_of_week=0):
    """Мок рабочих часов"""
    wh = MagicMock()
    wh.id = uuid.uuid4()
    wh.day_of_week = day_of_week
    wh.start_time = time(9, 0)
    wh.end_time = time(18, 0)
    wh.break_start = time(13, 0)
    wh.break_end = time(14, 0)
    wh.is_working_day = True
    return wh


def _make_exception_mock(exception_date=None, is_working_day=False):
    """Мок исключения из расписания"""
    exc = MagicMock()
    exc.id = uuid.uuid4()
    exc.exception_date = exception_date or date(2025, 3, 8)
    exc.is_working_day = is_working_day
    exc.start_time = time(10, 0) if is_working_day else None
    exc.end_time = time(16, 0) if is_working_day else None
    exc.reason = "Праздник"
    return exc


async def test_get_working_hours(owner_client):
    """Получение рабочих часов на все дни"""
    client, headers = owner_client
    mock_hours = [_make_working_hours_mock(day) for day in range(7)]

    with patch(
        "app.api.v1.schedule.schedule_service.get_working_hours", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_hours

        response = await client.get("/api/v1/schedule/hours", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7


async def test_update_working_hours(owner_client):
    """Обновление рабочих часов — upsert"""
    client, headers = owner_client
    updated_hours = [_make_working_hours_mock(0), _make_working_hours_mock(1)]

    with patch(
        "app.api.v1.schedule.schedule_service.update_working_hours", new_callable=AsyncMock
    ) as mock_update:
        mock_update.return_value = updated_hours

        response = await client.put(
            "/api/v1/schedule/hours",
            json=[
                {
                    "day_of_week": 0,
                    "start_time": "09:00:00",
                    "end_time": "18:00:00",
                    "is_working_day": True,
                },
                {
                    "day_of_week": 1,
                    "start_time": "09:00:00",
                    "end_time": "18:00:00",
                    "is_working_day": True,
                },
            ],
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_get_available_slots(owner_client):
    """Получение свободных слотов на дату"""
    client, headers = owner_client
    service_id = uuid.uuid4()
    mock_slots = [
        TimeSlot(start_time=time(9, 0), end_time=time(10, 0)),
        TimeSlot(start_time=time(10, 0), end_time=time(11, 0)),
        TimeSlot(start_time=time(14, 0), end_time=time(15, 0)),
    ]

    with patch(
        "app.api.v1.schedule.schedule_service.get_available_slots", new_callable=AsyncMock
    ) as mock_slots_fn:
        mock_slots_fn.return_value = mock_slots

        response = await client.get(
            f"/api/v1/schedule/slots?date=2025-03-17&service_id={service_id}",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["start_time"] == "09:00:00"


async def test_create_exception(owner_client):
    """Создание исключения в расписании"""
    client, headers = owner_client
    mock_exc = _make_exception_mock(exception_date=date(2025, 5, 1))

    with patch(
        "app.api.v1.schedule.schedule_service.create_exception", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_exc

        response = await client.post(
            "/api/v1/schedule/exceptions",
            json={
                "exception_date": "2025-05-01",
                "is_working_day": False,
                "reason": "Праздник",
            },
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["exception_date"] == "2025-05-01"
    assert data["is_working_day"] is False


async def test_delete_exception(owner_client):
    """Удаление исключения — 204"""
    client, headers = owner_client
    exception_id = uuid.uuid4()

    with patch(
        "app.api.v1.schedule.schedule_service.delete_exception", new_callable=AsyncMock
    ) as mock_delete:
        mock_delete.return_value = None

        response = await client.delete(
            f"/api/v1/schedule/exceptions/{exception_id}",
            headers=headers,
        )

    assert response.status_code == 204
