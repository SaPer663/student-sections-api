from os import environ as env

from pydantic import BaseModel, Field, PostgresDsn, field_validator
from typing import Literal


class Application(BaseModel):
    """Настройки приложения"""

    # Application
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

    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://student_user:student_pass@db:5432/student_sections_db",
        description="PostgreSQL connection string"
    )
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=0)
    DB_ECHO: bool = Field(default=False)

    @property
    def database_url_sync(self) -> str:
        """Синхронный URL для Alembic миграций"""
        return self.DATABASE_URL.replace("+asyncpg", "")


class Security(BaseModel):
    """Настройки безопасности."""

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT token generation"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)


class Pagination(BaseModel):
    """Настройки пагинации."""

    DEFAULT_PAGE_SIZE: int = Field(default=10, ge=1, le=100)
    MAX_PAGE_SIZE: int = Field(default=100, ge=1)


class Config(BaseModel):
    application: Application = Field(default_factory=lambda: Application(**env))
    database: Database = Field(default_factory=lambda: Database(**env))
    security: Security = Field(default_factory=lambda: Security(**env))
    pagination: Pagination = Field(default_factory=lambda: Pagination(**env))


settings = Config()
