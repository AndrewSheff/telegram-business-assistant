"""
Сервис для чатов — работа с сообщениями, хендоффами, ответами оператора.
Основной мост между ботом и админкой.
"""

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.chat_message import ChatMessage
from app.models.client import Client
from app.schemas.chat import ChatMessageResponse, HandoffClientResponse


async def get_active_handoffs(db: AsyncSession) -> list[HandoffClientResponse]:
    """
    Получаем список клиентов, ожидающих ответа оператора.
    Это те, у кого последнее сообщение с is_handoff=True
    и после него нет ответа от оператора.
    """
    # подзапрос — последнее сообщение каждого клиента с хендоффом
    handoff_messages = (
        select(ChatMessage.client_id)
        .where(ChatMessage.is_handoff == True)  # noqa: E712
        .distinct()
    )

    # берем клиентов с активным хендоффом
    # хендофф активен, если после сообщения с is_handoff=True нет ответа оператора
    result = await db.execute(handoff_messages)
    handoff_client_ids = [row[0] for row in result.all()]

    active_handoffs = []

    for client_id in handoff_client_ids:
        # находим последнее сообщение с is_handoff=True
        last_handoff_query = (
            select(ChatMessage)
            .where(
                and_(
                    ChatMessage.client_id == client_id,
                    ChatMessage.is_handoff == True,  # noqa: E712
                )
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        handoff_result = await db.execute(last_handoff_query)
        last_handoff = handoff_result.scalar_one_or_none()

        if last_handoff is None:
            continue

        # проверяем, есть ли ответ оператора после хендоффа
        operator_reply_query = (
            select(func.count())
            .select_from(ChatMessage)
            .where(
                and_(
                    ChatMessage.client_id == client_id,
                    ChatMessage.role == "operator",
                    ChatMessage.created_at > last_handoff.created_at,
                )
            )
        )
        reply_result = await db.execute(operator_reply_query)
        replies_count = reply_result.scalar() or 0

        if replies_count > 0:
            # оператор уже ответил — хендофф закрыт
            continue

        # считаем непрочитанные сообщения (от клиента после хендоффа)
        unread_query = (
            select(func.count())
            .select_from(ChatMessage)
            .where(
                and_(
                    ChatMessage.client_id == client_id,
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= last_handoff.created_at,
                )
            )
        )
        unread_result = await db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # последнее сообщение от клиента
        last_msg_query = (
            select(ChatMessage)
            .where(
                and_(
                    ChatMessage.client_id == client_id,
                    ChatMessage.role == "user",
                )
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_msg_result = await db.execute(last_msg_query)
        last_msg = last_msg_result.scalar_one_or_none()

        # тянем инфу о клиенте
        client_result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = client_result.scalar_one_or_none()

        if client is None:
            continue

        client_name = client.first_name
        if client.last_name:
            client_name += f" {client.last_name}"

        active_handoffs.append(
            HandoffClientResponse(
                client_id=client_id,
                client_name=client_name,
                telegram_username=client.username,
                last_message=last_msg.content if last_msg else None,
                unread_count=unread_count,
                created_at=last_handoff.created_at,
            )
        )

    # сортируем по времени хендоффа — самые давние первые (им надо ответить раньше)
    active_handoffs.sort(key=lambda x: x.created_at)

    return active_handoffs


async def get_messages(
    client_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 50,
) -> list[ChatMessageResponse]:
    """
    Последние сообщения клиента — для отображения в чате админки.
    Возвращаем в хронологическом порядке (старые первые).
    """
    # проверяем что клиент существует
    client_result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    if client_result.scalar_one_or_none() is None:
        raise NotFoundError("Клиент не найден")

    query = (
        select(ChatMessage)
        .where(ChatMessage.client_id == client_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    # переворачиваем для хронологического порядка
    return [
        ChatMessageResponse.model_validate(msg)
        for msg in reversed(messages)
    ]


async def log_message(
    client_id: uuid.UUID,
    role: str,
    content: str,
    is_handoff: bool,
    db: AsyncSession,
) -> ChatMessage:
    """
    Логируем сообщение — вызывается ботом при каждом входящем/исходящем сообщении.
    Роли: user, bot, operator.
    """
    message = ChatMessage(
        client_id=client_id,
        role=role,
        content=content,
        is_handoff=is_handoff,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def close_handoff(
    client_id: uuid.UUID,
    db: AsyncSession,
) -> ChatMessageResponse:
    """
    Закрываем хендофф — оператор завершил работу с клиентом.
    Добавляем системное сообщение, чтобы было видно в истории.
    """
    # проверяем что клиент существует
    client_result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    if client_result.scalar_one_or_none() is None:
        raise NotFoundError("Клиент не найден")

    # добавляем системное сообщение о закрытии
    message = ChatMessage(
        client_id=client_id,
        role="bot",
        content="Оператор завершил диалог. Бот снова на связи.",
        is_handoff=False,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return ChatMessageResponse.model_validate(message)
