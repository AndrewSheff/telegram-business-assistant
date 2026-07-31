"""
Сервис для работы с клиентами — поиск, обновление, история.
Тут же логика get_or_create для телеграм-бота.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.booking import Booking
from app.models.chat_message import ChatMessage
from app.models.client import Client
from app.schemas.client import ClientListResponse, ClientResponse, ClientUpdate


async def list_clients(
    db: AsyncSession,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
) -> ClientListResponse:
    """
    Список клиентов с пагинацией и поиском.
    Ищем по имени, фамилии и username через ILIKE — нечувствительно к регистру.
    """
    # базовый запрос — считаем бронирования подзапросом
    bookings_count_sq = (
        select(func.count(Booking.id))
        .where(Booking.client_id == Client.id)
        .correlate(Client)
        .scalar_subquery()
        .label("bookings_count")
    )

    query = select(Client, bookings_count_sq)

    # поиск по имени/фамилии/username — экранируем спецсимволы LIKE
    if search:
        escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like_pattern = f"%{escaped_search}%"
        query = query.where(
            or_(
                Client.first_name.ilike(like_pattern),
                Client.last_name.ilike(like_pattern),
                Client.username.ilike(like_pattern),
            )
        )

    # считаем общее количество
    count_query = select(func.count()).select_from(Client)
    if search:
        escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like_pattern = f"%{escaped_search}%"
        count_query = count_query.where(
            or_(
                Client.first_name.ilike(like_pattern),
                Client.last_name.ilike(like_pattern),
                Client.username.ilike(like_pattern),
            )
        )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # пагинация + сортировка (новые первые)
    offset = (page - 1) * size
    query = query.order_by(Client.created_at.desc()).offset(offset).limit(size)

    result = await db.execute(query)
    rows = result.all()

    # собираем ответ — раскидываем bookings_count в модель
    items = []
    for client, bookings_count in rows:
        client_resp = ClientResponse.model_validate(client)
        client_resp.bookings_count = bookings_count or 0
        items.append(client_resp)

    return ClientListResponse(items=items, total=total, page=page, size=size)


async def get_client(client_id: uuid.UUID, db: AsyncSession) -> ClientResponse:
    """
    Получаем одного клиента по id + считаем его бронирования.
    Если не нашли — 404, ничего тут не поделаешь.
    """
    bookings_count_sq = (
        select(func.count(Booking.id))
        .where(Booking.client_id == Client.id)
        .correlate(Client)
        .scalar_subquery()
        .label("bookings_count")
    )

    query = select(Client, bookings_count_sq).where(Client.id == client_id)
    result = await db.execute(query)
    row = result.one_or_none()

    if row is None:
        raise NotFoundError("Клиент не найден")

    client, bookings_count = row
    client_resp = ClientResponse.model_validate(client)
    client_resp.bookings_count = bookings_count or 0
    return client_resp


async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    db: AsyncSession,
) -> ClientResponse:
    """
    Обновляем инфу о клиенте — заметки, блокировка, телефон.
    Меняем только те поля, что реально пришли (не None).
    """
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if client is None:
        raise NotFoundError("Клиент не найден")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    # возвращаем с bookings_count
    return await get_client(client_id, db)


async def get_client_history(client_id: uuid.UUID, db: AsyncSession) -> dict:
    """
    История клиента — последние бронирования и сообщения в чате.
    Для быстрого обзора в админке, чтобы понимать контекст.
    """
    # проверяем что клиент существует
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise NotFoundError("Клиент не найден")

    # последние бронирования (10 штук)
    bookings_query = (
        select(Booking)
        .where(Booking.client_id == client_id)
        .order_by(Booking.booking_date.desc(), Booking.start_time.desc())
        .limit(10)
    )
    bookings_result = await db.execute(bookings_query)
    bookings = bookings_result.scalars().all()

    # последние сообщения (20 штук)
    messages_query = (
        select(ChatMessage)
        .where(ChatMessage.client_id == client_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()

    return {
        "bookings": bookings,
        "messages": list(reversed(messages)),  # хронологический порядок для чата
    }


async def get_or_create_by_telegram(
    telegram_id: int,
    first_name: str,
    last_name: str | None,
    username: str | None,
    db: AsyncSession,
) -> Client:
    """
    Ищем клиента по telegram_id, если нет — создаем нового.
    Используется ботом при каждом входящем сообщении.
    Заодно обновляем профильные данные — вдруг человек имя сменил.
    """
    result = await db.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )
    client = result.scalar_one_or_none()

    if client is not None:
        # обновляем профиль из телеги — мало ли, имя поменял
        client.first_name = first_name
        client.last_name = last_name
        client.username = username
        client.last_interaction_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(client)
        return client

    # новый клиент — добро пожаловать
    client = Client(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        last_interaction_at=datetime.now(UTC),
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client
