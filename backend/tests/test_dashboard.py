"""
Тесты дашборда — статистика, активность, топ услуг и вопросов.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from app.schemas.dashboard import ActivityPoint, DashboardStats, TopQuestion, TopService


async def test_get_stats(owner_client):
    """Основная статистика дашборда"""
    client, headers = owner_client
    mock_stats = DashboardStats(
        total_clients=150,
        new_clients_week=12,
        bookings_today=5,
        bookings_week=30,
        bookings_month=120,
        pending_handoffs=2,
    )

    with patch(
        "app.api.v1.dashboard.dashboard_service.get_stats", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_stats

        response = await client.get("/api/v1/dashboard/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_clients"] == 150
    assert data["bookings_today"] == 5
    assert data["pending_handoffs"] == 2


async def test_get_activity(owner_client):
    """График активности за последние дни"""
    client, headers = owner_client
    today = date.today()
    mock_activity = [
        ActivityPoint(date=today - timedelta(days=1), bookings=3, interactions=15),
        ActivityPoint(date=today, bookings=5, interactions=22),
    ]

    with patch(
        "app.api.v1.dashboard.dashboard_service.get_activity", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_activity

        response = await client.get("/api/v1/dashboard/activity?days=7", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[1]["bookings"] == 5


async def test_get_top_services(owner_client):
    """Топ популярных услуг"""
    client, headers = owner_client
    mock_top = [
        TopService(service_name="Стрижка", count=45),
        TopService(service_name="Маникюр", count=30),
        TopService(service_name="Покраска", count=15),
    ]

    with patch(
        "app.api.v1.dashboard.dashboard_service.get_top_services", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_top

        response = await client.get("/api/v1/dashboard/top-services?limit=3", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["service_name"] == "Стрижка"
    assert data[0]["count"] == 45


async def test_get_top_questions(owner_client):
    """Топ частых вопросов"""
    client, headers = owner_client
    mock_questions = [
        TopQuestion(question="Как записаться?", count=50),
        TopQuestion(question="Сколько стоит стрижка?", count=35),
    ]

    with patch(
        "app.api.v1.dashboard.dashboard_service.get_top_questions", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_questions

        response = await client.get("/api/v1/dashboard/top-questions?limit=5", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["count"] == 50
