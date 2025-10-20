from typing import Any


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, status_code: int, detail: Any = None) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(AppException):
    """Исключение когда сущность не найдена."""

    def __init__(self, entity: str, identifier: int | str) -> None:
        message = f"{entity} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404)


class AlreadyExistsException(AppException):
    """Исключение когда сущность уже существует."""

    def __init__(self, entity: str, field: str, value: str) -> None:
        message = f"{entity} with {field}='{value}' already exists"
        super().__init__(message, status_code=409)


class UnauthorizedException(AppException):
    """Исключение для неавторизованных запросов."""

    def __init__(self, message: str = "Could not validate credentials") -> None:
        super().__init__(message, status_code=403)


class ValidationException(AppException):
    """Исключение для ошибок валидации."""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message, status_code=422, detail=detail)
