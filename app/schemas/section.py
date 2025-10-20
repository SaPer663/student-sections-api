import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SectionBase(BaseModel):
    """Базовая схема секции."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    max_capacity: int = Field(default=20, ge=1, le=100)


class SectionCreate(SectionBase):
    """Схема для создания секции."""

    ...


class SectionUpdate(BaseModel):
    """Схема для обновления секции."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    max_capacity: int | None = Field(None, ge=1, le=100)


class StudentInSectionInfo(BaseModel):
    """Информация о студенте в секции."""

    model_config = ConfigDict(from_attributes=True)

    student_id: int
    first_name: str
    last_name: str
    email: str
    enrollment_date: datetime.date


class SectionResponse(SectionBase):
    """Схема ответа с данными секции."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    current_enrollment: int
    is_full: bool
    available_spots: int

    @model_validator(mode="before")
    @classmethod
    def calculate_enrollment_fields(cls, data: Any) -> Any:
        """
        Вычисление полей enrollment на основе данных модели.

        Ожидает модель SQLAlchemy с атрибутом _current_enrollment,
        который устанавливается в сервисе перед валидацией.
        """

        current_enrollment = data._current_enrollment
        max_capacity = data.max_capacity

        is_full = current_enrollment >= max_capacity
        available_spots = max(0, max_capacity - current_enrollment)

        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "max_capacity": max_capacity,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "current_enrollment": current_enrollment,
            "is_full": is_full,
            "available_spots": available_spots,
        }


class SectionDetailResponse(SectionBase):
    """Детальная схема секции со списком студентов."""

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    current_enrollment: int
    is_full: bool
    available_spots: int
    students: list[StudentInSectionInfo] = []
