"""
Обработчик очереди рассылок и пометка no-show.
Берет рассылки со статусом 'sending', батчами шлет сообщения,
обновляет счетчики и статусы.
"""

from datetime import UTC, date, datetime

import structlog
from sqlalchemy import and_, func, select

from app.database import async_session
from app.models.booking import Booking
from app.models.broadcast import Broadcast
from app.models.broadcast_log import BroadcastLog
from app.models.client import Client

logger = structlog.get_logger(__name__)

# Сколько сообщений берем за один прогон — не хотим спамить Telegram API
BATCH_SIZE = 30


async def process_broadcast_queue() -> None:
    """
    Основной воркер рассылок.
    Находит рассылки в статусе 'sending', берет батч из 30 необработанных логов,
    шлет каждому клиенту сообщение и обновляет статусы/счетчики.
    Когда все логи обработаны — ставим рассылке 'completed'.
    """
    from app.bot.bot import get_bot
    bot = get_bot()
    if bot is None:
        return

    async with async_session() as db:
        # Находим все активные рассылки
        broadcasts_query = select(Broadcast).where(Broadcast.status == "sending")
        broadcasts_result = await db.execute(broadcasts_query)
        active_broadcasts = broadcasts_result.scalars().all()

        for broadcast in active_broadcasts:
            # Берем батч необработанных логов
            logs_query = (
                select(BroadcastLog)
                .where(
                    and_(
                        BroadcastLog.broadcast_id == broadcast.id,
                        BroadcastLog.status == "pending",
                    )
                )
                .limit(BATCH_SIZE)
            )
            logs_result = await db.execute(logs_query)
            pending_logs = logs_result.scalars().all()

            if not pending_logs:
                # Все логи обработаны — завершаем рассылку
                broadcast.status = "completed"
                broadcast.completed_at = datetime.now(UTC)
                await db.commit()
                logger.info(
                    "broadcast_completed",
                    broadcast_id=str(broadcast.id),
                    sent=broadcast.sent_count,
                    failed=broadcast.failed_count,
                )
                continue

            # Обрабатываем каждый лог из батча
            for log_entry in pending_logs:
                # Подгружаем клиента
                client = await db.get(Client, log_entry.client_id)

                if not client:
                    log_entry.status = "failed"
                    log_entry.error_message = "Клиент не найден"
                    log_entry.sent_at = datetime.now(UTC)
                    broadcast.failed_count += 1
                    logger.warning(
                        "broadcast_client_not_found",
                        broadcast_id=str(broadcast.id),
                        client_id=str(log_entry.client_id),
                    )
                    continue

                try:
                    # Шлем сообщение через бот
                    if broadcast.image_url:
                        # Если есть картинка — шлем фото с подписью (лимит caption 1024 символа)
                        caption = broadcast.content
                        if len(caption) > 1024:
                            caption = caption[:1021] + "..."
                        await bot.send_photo(
                            chat_id=client.telegram_id,
                            photo=broadcast.image_url,
                            caption=caption,
                        )
                    else:
                        await bot.send_message(
                            chat_id=client.telegram_id,
                            text=broadcast.content,
                        )

                    log_entry.status = "sent"
                    log_entry.sent_at = datetime.now(UTC)
                    broadcast.sent_count += 1

                    logger.debug(
                        "broadcast_message_sent",
                        broadcast_id=str(broadcast.id),
                        client_id=str(client.id),
                    )

                except Exception as exc:
                    # Клиент заблочил бота, аккаунт удален и т.п. — пишем ошибку и идем дальше
                    log_entry.status = "failed"
                    log_entry.error_message = str(exc)[:500]
                    log_entry.sent_at = datetime.now(UTC)
                    broadcast.failed_count += 1

                    logger.warning(
                        "broadcast_message_failed",
                        broadcast_id=str(broadcast.id),
                        client_id=str(client.id),
                        error=str(exc),
                    )

            await db.commit()

            # Проверяем, все ли логи обработаны после этого батча
            remaining_query = select(func.count()).where(
                and_(
                    BroadcastLog.broadcast_id == broadcast.id,
                    BroadcastLog.status == "pending",
                )
            )
            remaining_result = await db.execute(remaining_query)
            remaining_count = remaining_result.scalar()

            if remaining_count == 0:
                broadcast.status = "completed"
                broadcast.completed_at = datetime.now(UTC)
                await db.commit()
                logger.info(
                    "broadcast_completed",
                    broadcast_id=str(broadcast.id),
                    sent=broadcast.sent_count,
                    failed=broadcast.failed_count,
                )


async def mark_no_show() -> None:
    """
    Помечаем неявки — если запись подтверждена, но дата уже прошла,
    значит клиент не пришел. Ставим статус 'no_show'.
    """
    today = date.today()

    async with async_session() as db:
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.status == "confirmed",
                    Booking.booking_date < today,
                )
            )
        )
        result = await db.execute(query)
        overdue_bookings = result.scalars().all()

        if not overdue_bookings:
            return

        for booking in overdue_bookings:
            booking.status = "no_show"
            logger.info(
                "booking_marked_no_show",
                booking_id=str(booking.id),
                booking_date=str(booking.booking_date),
            )

        await db.commit()
        logger.info("no_show_batch_done", count=len(overdue_bookings))
