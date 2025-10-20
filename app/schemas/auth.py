from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Схема запроса на логин."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Схема JWT токена."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные из JWT токена."""

    user_id: int | None = None
