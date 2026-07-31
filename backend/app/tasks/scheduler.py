"""
Планировщик фоновых задач на APScheduler.
Крутится в фоне, пока живо FastAPI-приложение, и периодически
гоняет напоминалки, рассылки и проверку неявок.
"""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks.broadcast_sender import mark_no_show, process_broadcast_queue
from app.tasks.reminders import send_reminders_2h, send_reminders_24h

logger = structlog.get_logger(__name__)

# Единственный экземпляр планировщика — переиспользуем между start/stop
scheduler: AsyncIOScheduler | None = None


async def start_scheduler() -> None:
    """
    Запускаем планировщик и регистрируем все джобы.
    Вызывается из lifespan FastAPI при старте.
    """
    global scheduler

    scheduler = AsyncIOScheduler()

    # Напоминалка за 24 часа — каждые 30 минут, чтобы не пропустить
    scheduler.add_job(
        send_reminders_24h,
        trigger=IntervalTrigger(minutes=30),
        id="send_reminders_24h",
        name="Напоминания за 24 часа",
        replace_existing=True,
    )

    # Напоминалка за 2 часа — почаще, каждые 15 минут
    scheduler.add_job(
        send_reminders_2h,
        trigger=IntervalTrigger(minutes=15),
        id="send_reminders_2h",
        name="Напоминания за 2 часа",
        replace_existing=True,
    )

    # Очередь рассылок — каждые 10 секунд, чтобы шустро раскидывать сообщения
    scheduler.add_job(
        process_broadcast_queue,
        trigger=IntervalTrigger(seconds=10),
        id="process_broadcast_queue",
        name="Обработка очереди рассылок",
        replace_existing=True,
    )

    # Пометка неявок — раз в час достаточно
    scheduler.add_job(
        mark_no_show,
        trigger=IntervalTrigger(hours=1),
        id="mark_no_show",
        name="Пометка неявок",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        jobs=[job.id for job in scheduler.get_jobs()],
    )


async def stop_scheduler() -> None:
    """
    Останавливаем планировщик при shutdown приложения.
    Ждем завершения текущих задач (wait=True), чтобы ничего не оборвать.
    """
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")

    scheduler = None
