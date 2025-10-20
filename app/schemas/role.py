import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """Базовая схема роли."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)


class RoleCreate(RoleBase):
    """Схема для создания роли."""

    ...


class RoleUpdate(BaseModel):
    """Схема для обновления роли."""

    name: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)


class RoleResponse(RoleBase):
    """Схема ответа с данными роли."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
