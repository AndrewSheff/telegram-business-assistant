"""
Тесты AI-сервиса — генерация ответов через Claude/OpenAI, фоллбек, хендофф.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_service import should_handoff

# -- Тесты should_handoff --


async def test_should_handoff_positive():
    """Фразы типа 'не знаю' должны триггерить хендофф"""
    assert should_handoff("Я не знаю ответа на этот вопрос") is True
    assert should_handoff("I don't know the answer") is True
    assert should_handoff("К сожалению, не могу ответить на этот вопрос") is True
    assert should_handoff("Обратитесь к оператору для уточнения") is True


async def test_should_handoff_negative():
    """Нормальные ответы не должны триггерить хендофф"""
    assert should_handoff("Стрижка стоит 1500 рублей") is False
    assert should_handoff("Мы работаем с 9 до 18") is False
    assert should_handoff("Записать вас на понедельник?") is False


async def test_generate_answer_claude():
    """Генерация ответа через Claude — мокаем anthropic"""
    # Мокаем содержимое ответа
    mock_content_block = MagicMock()
    mock_content_block.text = "Стрижка стоит 1500 рублей, длительность 60 минут."

    mock_message = MagicMock()
    mock_message.content = [mock_content_block]

    mock_anthropic_client = AsyncMock()
    mock_anthropic_client.messages.create = AsyncMock(return_value=mock_message)

    # Патчим импорт anthropic внутри функции _call_anthropic
    import types

    mock_anthropic_module = types.ModuleType("anthropic")
    mock_anthropic_module.AsyncAnthropic = MagicMock(return_value=mock_anthropic_client)

    with (
        patch.dict("sys.modules", {"anthropic": mock_anthropic_module}),
        patch("app.services.ai_service.settings") as mock_settings,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"

        from app.services.ai_service import _call_anthropic

        result = await _call_anthropic("system prompt", "Сколько стоит стрижка?")

    assert result == "Стрижка стоит 1500 рублей, длительность 60 минут."


async def test_generate_answer_openai():
    """Генерация ответа через OpenAI — мокаем openai"""
    mock_choice = MagicMock()
    mock_choice.message.content = "Мы находимся по адресу ул. Ленина 42"

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

    import types

    mock_openai_module = types.ModuleType("openai")
    mock_openai_module.AsyncOpenAI = MagicMock(return_value=mock_openai_client)

    with (
        patch.dict("sys.modules", {"openai": mock_openai_module}),
        patch("app.services.ai_service.settings") as mock_settings,
    ):
        mock_settings.OPENAI_API_KEY = "test-key"

        from app.services.ai_service import _call_openai

        result = await _call_openai("system prompt", "Где вы находитесь?")

    assert result == "Мы находимся по адресу ул. Ленина 42"


async def test_generate_answer_fallback():
    """Если AI недоступен — возвращаем вежливый фоллбек"""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    with (
        patch("app.services.ai_service._call_anthropic", new_callable=AsyncMock) as mock_claude,
        patch("app.services.ai_service._call_openai", new_callable=AsyncMock) as mock_gpt,
    ):
        # Оба провайдера упали
        mock_claude.side_effect = Exception("API unavailable")
        mock_gpt.side_effect = Exception("API unavailable")

        from app.services.ai_service import generate_answer

        result = await generate_answer("Тестовый вопрос", mock_db)

    # Должен вернуть dict с answer и should_handoff
    assert isinstance(result, dict)
    assert "answer" in result
    assert "should_handoff" in result
    assert "недоступен" in result["answer"] or "попробуйте" in result["answer"].lower()
    assert result["should_handoff"] is True
