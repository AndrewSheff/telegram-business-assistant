from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфиг приложения — тянем все из .env, ничего не хардкодим"""

    # БД
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/tg_business_bot"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-to-a-random-32-char-string"  # noqa: S105
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Первоначальный админ (owner)
    ADMIN_EMAIL: str = "admin@company.com"
    ADMIN_NAME: str = "Admin"
    ADMIN_DEFAULT_PASSWORD: str = "ChangeMe123"  # noqa: S105

    # AI-провайдеры
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Приложение
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost"]
    TIMEZONE: str = "UTC"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
