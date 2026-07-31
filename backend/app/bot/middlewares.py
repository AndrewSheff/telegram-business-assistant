"""
Мидлвари для бота — перехватывают каждое сообщение/коллбэк
и подкидывают в хендлер нужные штуки: сессию БД и клиента.
"""

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.database import async_session
from app.services import client_service

logger = structlog.get_logger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """
    Мидлварь для инъекции сессии БД.
    Создаем сессию на каждый апдейт и кладем в data["db"].
    Хендлер получает готовую сессию, не паримся.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["db"] = session
            return await handler(event, data)


class UserRegistrationMiddleware(BaseMiddleware):
    """
    Мидлварь для авто-регистрации клиентов.
    На каждое сообщение/коллбэк — get_or_create клиента по telegram_id.
    Результат кладем в data["client"] — хендлеры достают оттуда.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Вытаскиваем юзера из события (Message или CallbackQuery)
        user = None
        if isinstance(event, Message | CallbackQuery) and event.from_user:
            user = event.from_user

        if user is None:
            # Нет юзера — ну и ладно, бывает (каналы, группы и т.д.)
            return await handler(event, data)

        db = data.get("db")
        if db is None:
            # Если БД-мидлварь ещё не отработал — пропускаем
            logger.warning("db_session_not_found_in_middleware")
            return await handler(event, data)

        # Создаем или обновляем клиента
        client = await client_service.get_or_create_by_telegram(
            telegram_id=user.id,
            first_name=user.first_name or "Unknown",
            last_name=user.last_name,
            username=user.username,
            db=db,
        )

        data["client"] = client

        return await handler(event, data)
