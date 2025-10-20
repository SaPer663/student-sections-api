from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SortOrder(str, Enum):
    """Порядок сортировки."""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Параметры пагинации."""

    offset: int = Field(default=0, ge=0, description="Количество записей для пропуска")
    limit: int = Field(
        default=10, ge=1, le=100, description="Максимально количество записей для вывода"
    )


class SortParams(BaseModel):
    """Параметры сортировки."""

    sort_by: str = Field(default="id", description="Поле, по которому производится сортировка")
    order: SortOrder = Field(default=SortOrder.ASC, description="Тип сортировки (asc or desc)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic схема для пагинированного ответа."""

    items: list[T]
    total: int = Field(..., description="Общее количество элементов")
    offset: int = Field(..., description="Количество пропущенных элементов")
    limit: int = Field(..., description="Максимальное количество элементов на странице")

    @property
    def has_more(self) -> bool:
        """Есть ли еще записи."""
        return self.offset + self.limit < self.total

    @property
    def page(self) -> int:
        """Текущая страница (начиная с 1)."""
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1

    @property
    def total_pages(self) -> int:
        """Общее количество страниц."""
        return (self.total + self.limit - 1) // self.limit if self.limit > 0 else 1


class StudentFilterParams(BaseModel):
    """Параметры фильтрации для студентов."""

    search: str | None = Field(None, description="Поиск по полям: first name, last name, or email")
    section_id: int | None = Field(None, description="Фильтер по ID секции")


class SectionFilterParams(BaseModel):
    """Параметры фильтрации для секций."""

    search: str | None = Field(None, description="Поиск по полям: name or description")
    available_only: bool = Field(
        False, description="Флаг, показывать только доступные для зачисления секции"
    )
