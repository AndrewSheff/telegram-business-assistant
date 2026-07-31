"""
Модель пользователя админки — владелец бизнеса или оператор.
Роли: owner (главный), operator (помощник).
"""

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """
    Юзеры админ-панели — те, кто рулят ботом.
    Owner может все, operator — ограниченный набор действий.
    """

    __tablename__ = "users"

    # Почта — она же логин, дубликатов быть не должно
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Имя для отображения
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Хеш пароля — храним только хеш, конечно
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Роль: owner или operator
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="operator")

    # Активен ли аккаунт — можно заблочить без удаления
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Флаг — при первом входе надо сменить пароль
    must_change_password: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Рассылки, которые создал этот юзер
    broadcasts: Mapped[list["Broadcast"]] = relationship(  # noqa: F821
        back_populates="creator", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'operator')",
            name="ck_users_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
