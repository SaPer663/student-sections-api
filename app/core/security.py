from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля.

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из БД

    Returns:
        True если пароль совпадает, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширование пароля.

    Args:
        password: Пароль в открытом виде

    Returns:
        Хешированный пароль
    """
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Создание JWT access токена.

    Args:
        data: Данные для кодирования в токен (обычно {"sub": user_id})
        expires_delta: Время жизни токена (если не указано, берется из настроек)

    Returns:
        JWT токен
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.security.SECRET_KEY, algorithm=settings.security.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Декодирование JWT токена.

    Args:
        token: JWT токен

    Returns:
        Декодированные данные из токена или None при ошибке
    """
    try:
        payload = jwt.decode(
            token, settings.security.SECRET_KEY, algorithms=[settings.security.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
