"""
Сервис дашборда — статистика, графики, топы.
Собираем все самое важное для главной страницы админки.
"""

from datetime import date, timedelta

from sqlalchemy import Date, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.chat_message import ChatMessage
from app.models.client import Client
from app.schemas.dashboard import ActivityPoint, DashboardStats, TopQuestion, TopService


async def get_stats(db: AsyncSession) -> DashboardStats:
    """
    Основная статистика — все цифры для карточек на дашборде.
    Считаем клиентов, бронирования, хендоффы.
    """
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # общее количество клиентов
    total_clients_result = await db.execute(
        select(func.count()).select_from(Client)
    )
    total_clients = total_clients_result.scalar() or 0

    # новые клиенты за неделю
    new_clients_result = await db.execute(
        select(func.count())
        .select_from(Client)
        .where(cast(Client.created_at, Date) >= week_ago)
    )
    new_clients_week = new_clients_result.scalar() or 0

    # бронирования сегодня
    bookings_today_result = await db.execute(
        select(func.count())
        .select_from(Booking)
        .where(Booking.booking_date == today)
    )
    bookings_today = bookings_today_result.scalar() or 0

    # бронирования за неделю
    bookings_week_result = await db.execute(
        select(func.count())
        .select_from(Booking)
        .where(Booking.booking_date >= week_ago)
    )
    bookings_week = bookings_week_result.scalar() or 0

    # бронирования за месяц
    bookings_month_result = await db.execute(
        select(func.count())
        .select_from(Booking)
        .where(Booking.booking_date >= month_ago)
    )
    bookings_month = bookings_month_result.scalar() or 0

    # количество активных хендоффов (сообщения с is_handoff=True без ответа оператора)
    # упрощенный вариант — просто считаем уникальных клиентов с активным хендоффом
    handoff_clients = (
        select(ChatMessage.client_id)
        .where(ChatMessage.is_handoff == True)  # noqa: E712
        .distinct()
    )
    handoff_result = await db.execute(handoff_clients)
    handoff_client_ids = [row[0] for row in handoff_result.all()]

    pending_handoffs = 0
    for client_id in handoff_client_ids:
        # последний хендофф
        last_handoff_query = (
            select(ChatMessage.created_at)
            .where(
                and_(
                    ChatMessage.client_id == client_id,
                    ChatMessage.is_handoff == True,  # noqa: E712
                )
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        handoff_ts_result = await db.execute(last_handoff_query)
        handoff_ts = handoff_ts_result.scalar_one_or_none()

        if handoff_ts is None:
            continue

        # есть ли ответ оператора после хендоффа
        operator_reply_query = (
            select(func.count())
            .select_from(ChatMessage)
            .where(
                and_(
                    ChatMessage.client_id == client_id,
                    ChatMessage.role == "operator",
                    ChatMessage.created_at > handoff_ts,
                )
            )
        )
        reply_result = await db.execute(operator_reply_query)
        if (reply_result.scalar() or 0) == 0:
            pending_handoffs += 1

    return DashboardStats(
        total_clients=total_clients,
        new_clients_week=new_clients_week,
        bookings_today=bookings_today,
        bookings_week=bookings_week,
        bookings_month=bookings_month,
        pending_handoffs=pending_handoffs,
    )


async def get_activity(
    db: AsyncSession,
    days: int = 30,
) -> list[ActivityPoint]:
    """
    График активности — по дням за последние N дней.
    Считаем бронирования и сообщения (взаимодействия) на каждый день.
    """
    start_date = date.today() - timedelta(days=days)

    # бронирования по дням
    bookings_query = (
        select(
            Booking.booking_date.label("day"),
            func.count(Booking.id).label("count"),
        )
        .where(Booking.booking_date >= start_date)
        .group_by(Booking.booking_date)
    )
    bookings_result = await db.execute(bookings_query)
    bookings_by_day = {row.day: row.count for row in bookings_result.all()}

    # сообщения (взаимодействия) по дням
    interactions_query = (
        select(
            cast(ChatMessage.created_at, Date).label("day"),
            func.count(ChatMessage.id).label("count"),
        )
        .where(cast(ChatMessage.created_at, Date) >= start_date)
        .group_by(cast(ChatMessage.created_at, Date))
    )
    interactions_result = await db.execute(interactions_query)
    interactions_by_day = {row.day: row.count for row in interactions_result.all()}

    # собираем результат — заполняем нулями дни без данных
    points = []
    current = start_date
    today = date.today()

    while current <= today:
        points.append(
            ActivityPoint(
                date=current,
                bookings=bookings_by_day.get(current, 0),
                interactions=interactions_by_day.get(current, 0),
            )
        )
        current += timedelta(days=1)

    return points


async def get_top_services(
    db: AsyncSession,
    limit: int = 5,
) -> list[TopService]:
    """Топ услуг по количеству бронирований — для рейтинга в админке."""
    from app.models.service import Service

    query = (
        select(
            Service.name.label("service_name"),
            func.count(Booking.id).label("count"),
        )
        .join(Service, Booking.service_id == Service.id)
        .group_by(Service.name)
        .order_by(func.count(Booking.id).desc())
        .limit(limit)
    )
    result = await db.execute(query)

    return [
        TopService(service_name=row.service_name, count=row.count)
        for row in result.all()
    ]


async def get_top_questions(
    db: AsyncSession,
    limit: int = 5,
) -> list[TopQuestion]:
    """
    Топ вопросов от клиентов — группируем по содержимому.
    Помогает понять, что интересует клиентов больше всего.
    """
    query = (
        select(
            ChatMessage.content.label("question"),
            func.count(ChatMessage.id).label("count"),
        )
        .where(ChatMessage.role == "user")
        .group_by(ChatMessage.content)
        .order_by(func.count(ChatMessage.id).desc())
        .limit(limit)
    )
    result = await db.execute(query)

    return [
        TopQuestion(question=row.question, count=row.count)
        for row in result.all()
    ]
