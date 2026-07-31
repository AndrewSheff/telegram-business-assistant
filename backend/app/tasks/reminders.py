"""
Напоминалки о записях — отправляем клиентам за 24 часа и за 2 часа до визита.
Работают через планировщик, крутятся в фоне и не мешают основному приложению.
"""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import and_, select

from app.database import async_session
from app.models.booking import Booking
from app.models.client import Client
from app.models.service import Service

logger = structlog.get_logger(__name__)


async def send_reminders_24h() -> None:
    """
    Напоминание за 24 часа до записи.
    Ищем букинги в окне +-30 минут от текущего момента + 24 часа,
    у которых reminder_24h_sent еще False. Шлем клиенту и помечаем.
    """
    from app.bot.bot import get_bot
    bot = get_bot()
    if bot is None:
        return

    now = datetime.now(UTC)
    target_time = now + timedelta(hours=24)
    window_start = target_time - timedelta(minutes=30)
    window_end = target_time + timedelta(minutes=30)

    async with async_session() as db:
        # Ищем записи, которые попадают в окно и ещё не получали напоминание
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.reminder_24h_sent == False,  # noqa: E712
                    Booking.status.in_(["pending", "confirmed"]),
                    # Собираем datetime из даты + времени и проверяем попадание в окно
                    Booking.booking_date >= window_start.date(),
                    Booking.booking_date <= window_end.date(),
                )
            )
            .options()
        )
        result = await db.execute(query)
        bookings = result.scalars().all()

        sent_count = 0
        for booking in bookings:
            # Собираем полный datetime записи для точной проверки окна
            booking_dt = datetime.combine(booking.booking_date, booking.start_time)
            if not (window_start <= booking_dt <= window_end):
                continue

            # Подгружаем клиента и услугу для текста сообщения
            client = await db.get(Client, booking.client_id)
            service = await db.get(Service, booking.service_id)

            if not client or not service:
                logger.warning(
                    "reminder_skip_missing_data",
                    booking_id=str(booking.id),
                )
                continue

            # Формируем красивый текст напоминания
            message_text = (
                f"Напоминаем о вашей записи завтра!\n\n"
                f"Услуга: {service.name}\n"
                f"Дата: {booking.booking_date.strftime('%d.%m.%Y')}\n"
                f"Время: {booking.start_time.strftime('%H:%M')}\n\n"
                f"Ждем вас!"
            )

            try:
                await bot.send_message(
                    chat_id=client.telegram_id,
                    text=message_text,
                )
                booking.reminder_24h_sent = True
                sent_count += 1
                logger.info(
                    "reminder_24h_sent",
                    booking_id=str(booking.id),
                    client_id=str(client.id),
                )
            except Exception as exc:
                # Клиент заблокировал бота или что-то пошло не так — не падаем
                logger.warning(
                    "reminder_24h_failed",
                    booking_id=str(booking.id),
                    client_id=str(client.id),
                    error=str(exc),
                )

        await db.commit()

        if sent_count > 0:
            logger.info("reminders_24h_batch_done", sent=sent_count)


async def send_reminders_2h() -> None:
    """
    Напоминание за 2 часа до записи.
    Та же логика, что и для 24-часового, только окно поменьше — +-15 мин.
    """
    from app.bot.bot import get_bot
    bot = get_bot()
    if bot is None:
        return

    now = datetime.now(UTC)
    target_time = now + timedelta(hours=2)
    window_start = target_time - timedelta(minutes=15)
    window_end = target_time + timedelta(minutes=15)

    async with async_session() as db:
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.reminder_2h_sent == False,  # noqa: E712
                    Booking.status.in_(["pending", "confirmed"]),
                    Booking.booking_date >= window_start.date(),
                    Booking.booking_date <= window_end.date(),
                )
            )
            .options()
        )
        result = await db.execute(query)
        bookings = result.scalars().all()

        sent_count = 0
        for booking in bookings:
            booking_dt = datetime.combine(booking.booking_date, booking.start_time)
            if not (window_start <= booking_dt <= window_end):
                continue

            client = await db.get(Client, booking.client_id)
            service = await db.get(Service, booking.service_id)

            if not client or not service:
                logger.warning(
                    "reminder_skip_missing_data",
                    booking_id=str(booking.id),
                )
                continue

            message_text = (
                f"Через 2 часа у вас запись!\n\n"
                f"Услуга: {service.name}\n"
                f"Время: {booking.start_time.strftime('%H:%M')}\n\n"
                f"До встречи!"
            )

            try:
                await bot.send_message(
                    chat_id=client.telegram_id,
                    text=message_text,
                )
                booking.reminder_2h_sent = True
                sent_count += 1
                logger.info(
                    "reminder_2h_sent",
                    booking_id=str(booking.id),
                    client_id=str(client.id),
                )
            except Exception as exc:
                logger.warning(
                    "reminder_2h_failed",
                    booking_id=str(booking.id),
                    client_id=str(client.id),
                    error=str(exc),
                )

        await db.commit()

        if sent_count > 0:
            logger.info("reminders_2h_batch_done", sent=sent_count)
