"""
API для чата — хендоффы, сообщения, ответы оператора.
Все эндпоинты требуют авторизации (owner или operator).
"""

import uuid

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.client import Client
from app.schemas.chat import ChatMessageResponse, HandoffClientResponse, OperatorReplyRequest
from app.services import chat_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Чат"])


@router.get("/active", response_model=list[HandoffClientResponse])
async def get_active_handoffs(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Список клиентов, ожидающих ответа оператора."""
    return await chat_service.get_active_handoffs(db)


@router.get("/{client_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """История сообщений с клиентом — последние 50 штук."""
    return await chat_service.get_messages(client_id, db)


@router.post("/{client_id}/reply", response_model=ChatMessageResponse)
async def reply_to_client(
    client_id: uuid.UUID,
    data: OperatorReplyRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """
    Ответ оператора клиенту — логируем в БД и отправляем через Telegram-бота.
    """
    message = await chat_service.log_message(
        client_id=client_id,
        role="operator",
        content=data.content,
        is_handoff=False,
        db=db,
    )

    # Отправляем сообщение клиенту в Telegram
    try:
        from app.bot.bot import get_bot
        bot = get_bot()
        if bot:
            client_result = await db.execute(
                select(Client).where(Client.id == client_id)
            )
            client = client_result.scalar_one_or_none()
            if client and client.telegram_id:
                await bot.send_message(
                    chat_id=client.telegram_id,
                    text=f"Ответ оператора:\n\n{data.content}",
                )
    except Exception as e:
        # Не падаем если не удалось отправить — сообщение все равно сохранено
        logger.warning("operator_reply_telegram_failed", error=str(e), client_id=str(client_id))

    return ChatMessageResponse.model_validate(message)


@router.post("/{client_id}/close", response_model=ChatMessageResponse)
async def close_handoff(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Закрыть хендофф — оператор завершил работу с клиентом."""
    return await chat_service.close_handoff(client_id, db)
