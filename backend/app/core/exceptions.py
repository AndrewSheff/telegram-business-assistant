from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class AppError(HTTPException):
    """Базовая ошибка приложения — все кастомные наследуются от нее"""

    def __init__(self, status_code: int = 400, detail: str = "Something went wrong"):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppError):
    """Не нашли — 404"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(AppError):
    """Конфликт — 409 (дубликат, занятый слот и т.д.)"""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedError(AppError):
    """Неавторизован — 401 (неверные credentials)"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(AppError):
    """Нет прав — 403"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Обработчик наших кастомных ошибок"""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Обработчик ошибок валидации Pydantic"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": errors})
