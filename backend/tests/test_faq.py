"""
Тесты FAQ — список, создание, обновление, удаление.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from app.schemas.faq import FaqResponse


def _make_faq_response(faq_id=None, question="Как оплатить?", answer="Картой или наличными"):
    """Собираем FaqResponse для моков"""
    return FaqResponse(
        id=faq_id or uuid.uuid4(),
        question=question,
        answer=answer,
        category="Оплата",
        sort_order=0,
        is_active=True,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


async def test_list_faq(owner_client):
    """Список FAQ"""
    client, headers = owner_client
    mock_faqs = [
        _make_faq_response(question="Как оплатить?"),
        _make_faq_response(question="Где вы находитесь?", answer="ул. Ленина 42"),
    ]

    with patch("app.api.v1.faq.faq_service.list_faq", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_faqs

        response = await client.get("/api/v1/faq", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["question"] == "Как оплатить?"


async def test_create_faq(owner_client):
    """Создание FAQ — только owner"""
    client, headers = owner_client
    new_faq = _make_faq_response(question="Есть ли парковка?", answer="Да, бесплатная")

    with patch("app.api.v1.faq.faq_service.create_faq", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = new_faq

        response = await client.post(
            "/api/v1/faq",
            json={
                "question": "Есть ли парковка?",
                "answer": "Да, бесплатная",
                "category": "Общее",
            },
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["question"] == "Есть ли парковка?"


async def test_update_faq(owner_client):
    """Обновление FAQ"""
    client, headers = owner_client
    faq_id = uuid.uuid4()
    updated_faq = _make_faq_response(faq_id=faq_id, answer="Только картой")

    with patch("app.api.v1.faq.faq_service.update_faq", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = updated_faq

        response = await client.put(
            f"/api/v1/faq/{faq_id}",
            json={"answer": "Только картой"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Только картой"


async def test_delete_faq(owner_client):
    """Удаление FAQ — 204"""
    client, headers = owner_client
    faq_id = uuid.uuid4()

    with patch("app.api.v1.faq.faq_service.delete_faq", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = None

        response = await client.delete(
            f"/api/v1/faq/{faq_id}",
            headers=headers,
        )

    assert response.status_code == 204
