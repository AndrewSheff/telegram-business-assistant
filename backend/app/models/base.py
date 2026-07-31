"""
Базовая модель — от нее наследуются все остальные.
Тут id (UUID), created_at, updated_at с автообновлением.
"""

import uuid
from datetime import datetime

from sqlalchemy import event, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Корневой класс для всех моделей, DeclarativeBase из SQLAlchemy 2.0"""

    pass


class BaseModel(Base):
    """
    Абстрактная базовая модель — id + временные метки.
    Все таблицы наследуются от нее, чтобы не дублировать одно и то же.
    """

    __abstract__ = True

    # Уникальный идентификатор, генерится на стороне Postgres
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Когда создали запись
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )

    # Когда последний раз обновляли — проставляется автоматом через event listener
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )


def _set_updated_at(mapper, connection, target):
    """Листенер — при любом UPDATE автоматически обновляет updated_at"""
    from datetime import UTC
    target.updated_at = datetime.now(UTC)


# Подключаем листенер ко всем наследникам BaseModel
event.listen(BaseModel, "before_update", _set_updated_at, propagate=True)
