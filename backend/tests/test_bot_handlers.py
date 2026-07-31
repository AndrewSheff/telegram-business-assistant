"""
Тесты бот-хендлеров — базовые проверки логики обработчиков.
Полноценные интеграционные тесты с aiogram тут не делаем,
проверяем что функции существуют и основная логика работает.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch


async def test_start_handler_exists():
    """Проверяем что хендлер /start существует и вызываемый"""
    from app.bot.handlers.start import cmd_start

    assert callable(cmd_start)

    # Мокаем все зависимости
    message = AsyncMock()
    message.answer = AsyncMock()
    db = AsyncMock()
    client = MagicMock()
    client.first_name = "Тестовый"
    client.telegram_id = 123456
    state = AsyncMock()

    # Мокаем settings_service
    mock_settings = MagicMock()
    mock_settings.welcome_message = "Привет, {name}!"

    with patch("app.bot.handlers.start.settings_service.get_settings", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_settings

        await cmd_start(message, db, client, state)

    # Проверяем что бот отправил ответ
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    # В тексте должно быть имя клиента
    assert "Тестовый" in call_args[0][0] or "Тестовый" in str(call_args)


async def test_services_list_handler_exists():
    """Проверяем что хендлер списка услуг существует и корректно работает"""
    from app.bot.handlers.services import show_services

    assert callable(show_services)

    # Мокаем — price должен быть числом, т.к. сервис форматирует его через :.0f
    message = AsyncMock()
    message.answer = AsyncMock()
    db = AsyncMock()

    mock_service = MagicMock()
    mock_service.id = uuid.uuid4()
    mock_service.name = "Стрижка"
    mock_service.price = Decimal("1500")  # реальное число, не MagicMock
    mock_services = [mock_service]

    with patch(
        "app.bot.handlers.services.service_service.list_services", new_callable=AsyncMock
    ) as mock_list:
        mock_list.return_value = mock_services

        await show_services(message, db)

    # Бот должен отправить ответ с клавиатурой
    message.answer.assert_called_once()


async def test_services_list_empty():
    """Если услуг нет — бот скажет что пока нет"""
    from app.bot.handlers.services import show_services

    message = AsyncMock()
    message.answer = AsyncMock()
    db = AsyncMock()

    with patch(
        "app.bot.handlers.services.service_service.list_services", new_callable=AsyncMock
    ) as mock_list:
        mock_list.return_value = []

        await show_services(message, db)

    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "нет" in call_text.lower()
