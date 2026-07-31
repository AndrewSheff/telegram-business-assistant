"""Схемы для аутентификации и всего что с ней связано."""

from pydantic import BaseModel, ConfigDict, field_validator


class LoginRequest(BaseModel):
    """Запрос на вход — классика: почта + пароль."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Ответ после успешного логина — токен и инфа о юзере."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    user: "UserResponse"


class ChangePasswordRequest(BaseModel):
    """Смена пароля — старый, новый и подтверждение, чтоб не промахнуться."""

    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Проверяем что новый пароль и подтверждение совпадают, а то мало ли."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Пароли не совпадают")
        return v

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Проверяем пароль на адекватность — длина, цифры, разный регистр."""
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        return v


# чтоб не было проблем с циклическим импортом
from app.schemas.user import UserResponse  # noqa: E402, TC001

LoginResponse.model_rebuild()
