from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas import RoleResponse


def validate_password_strength(password: str | None) -> str | None:
    """
    Валидация надежности пароля.

    Проверяет что пароль содержит: минимум одну цифру и минимум одну букву

    Args:
        v: Пароль для проверки

    Returns:
        Валидный пароль

    Raises:
        ValueError: Если пароль не соответствует требованиям
    """
    if password is None:
        return password

    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")
    if not any(char.isalpha() for char in password):
        raise ValueError("Password must contain at least one letter")

    return password


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Схема для создания пользователя (регистрация обычного пользователя)."""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация пароля - должен содержать буквы и цифры."""

        return validate_password_strength(password=v)


class UserCreateByAdmin(UserBase):
    """Схема для создания пользователя администратором."""

    password: str = Field(..., min_length=8, max_length=100)
    role_id: int = Field(..., description="ID роли пользователя", ge=1)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация пароля - должен содержать буквы и цифры."""

        return validate_password_strength(password=v)


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""

    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=100)
    role_id: int | None = Field(None, ge=1)
    is_active: bool | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Валидация пароля при обновлении."""

        return validate_password_strength(password=v)


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: RoleResponse
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserResponse):
    """Схема пользователя в БД (с хешированным паролем)."""

    hashed_password: str
