from os import environ as env
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, PostgresDsn, field_validator


class Application(BaseModel):
    """Настройки приложения"""

    APP_NAME: str = "Student Sections API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = Field(default=True)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: str | bool) -> bool:
        """Парсинг DEBUG из строки или bool"""
        if isinstance(v, bool):
            return v
        return v.lower() in ("true", "1", "yes")

    @property
    def is_development(self) -> bool:
        """Проверка режима разработки"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Проверка продакшен режима"""
        return self.ENVIRONMENT == "production"


class Database(BaseModel):
    """Настройки базы данных."""

    POSTGRES_USER: str = Field(default="student_user")
    POSTGRES_PASSWORD: str = Field(default="student_pass")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_DB: str = Field(default="student_sections_db")
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=0)
    DB_ECHO: bool = Field(default=False)

    @property
    def database_url_async(self) -> PostgresDsn:
        """Асинхронный PostgreSQL connection string для SQLAlchemy"""
        return PostgresDsn(
            url=(
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:5432/{self.POSTGRES_DB}"
            )
        )

    @property
    def database_url_sync(self) -> str:
        """Синхронный URL для Alembic миграций"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:5432/{self.POSTGRES_DB}"
        )


class Security(BaseModel):
    """Настройки безопасности."""

    SECRET_KEY: str = Field(..., min_length=32, description="Secret key for JWT token generation")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)


class InitialAdmin(BaseModel):
    """Настройки первого администратора."""

    ADMIN_EMAIL: EmailStr = Field(
        default="admin@example.com", description="Email первого администратора"
    )
    ADMIN_PASSWORD: str = Field(
        default="admin123", min_length=8, description="Пароль первого администратора"
    )
    ADMIN_FULL_NAME: str = Field(
        default="System Administrator", description="Полное имя первого администратора"
    )


class Pagination(BaseModel):
    """Настройки пагинации."""

    DEFAULT_PAGE_SIZE: int = Field(default=10, ge=1, le=100)
    MAX_PAGE_SIZE: int = Field(default=100, ge=1)


class Config(BaseModel):
    application: Application = Field(default_factory=lambda: Application(**env))
    database: Database = Field(default_factory=lambda: Database(**env))
    security: Security = Field(default_factory=lambda: Security(**env))
    initial_admin: InitialAdmin = Field(default_factory=lambda: InitialAdmin(**env))
    pagination: Pagination = Field(default_factory=lambda: Pagination(**env))


settings = Config()
