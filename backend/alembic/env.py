"""
Alembic env — асинхронная конфигурация для asyncpg.
Подтягивает все модели и перебивает url из настроек приложения.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.config import settings

# Импортируем все модели, чтобы Alembic видел их при autogenerate
from app.models import (  # noqa: F401
    Booking,
    Broadcast,
    BroadcastLog,
    BusinessSettings,
    ChatMessage,
    Client,
    FaqItem,
    KnowledgeBlock,
    ScheduleException,
    Service,
    ServiceCategory,
    User,
    WorkingHours,
)
from app.models.base import Base

# Конфиг Alembic из .ini файла
config = context.config

# Настраиваем логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate — берем из нашей Base
target_metadata = Base.metadata

# Перебиваем url из настроек приложения, чтобы не дублировать в .ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Миграции в оффлайн-режиме — генерит SQL без подключения к БД.
    Полезно для генерации скриптов на проде.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Запускаем миграции с уже готовым соединением"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Асинхронный запуск миграций — создаем async engine и гоняем через него.
    Используем NullPool, чтобы не было проблем с пулом при миграциях.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Онлайн-режим — подключаемся к БД и мигрируем"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
