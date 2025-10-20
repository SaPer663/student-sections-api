from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовый репозиторий для работы с БД.

    Реализует основные CRUD операции с поддержкой фильтрации, сортировки и пагинации.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:

        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        """
        Получить сущность по ID.

        Args:
            id: Идентификатор сущности

        Returns:
            Найденная сущность или None
        """
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        sort_by: str = "id",
        order: str = "asc",
    ) -> Sequence[ModelType]:
        """
        Получить список сущностей с фильтрацией, сортировкой и пагинацией.

        Args:
            offset: Количество записей для пропуска
            limit: Максимальное количество записей
            filters: Словарь фильтров {field: value}
            sort_by: Поле для сортировки
            order: Порядок сортировки ('asc' или 'desc')

        Returns:
            Список сущностей
        """
        query = select(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)

        if hasattr(self.model, sort_by):
            sort_column = getattr(self.model, sort_by)
            query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())

        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Подсчет количества записей с учетом фильтров.

        Args:
            filters: Словарь фильтров {field: value}

        Returns:
            Количество записей
        """
        query = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Создать новую сущность.

        Args:
            obj_in: Pydantic схема с данными для создания

        Returns:
            Созданная сущность
        """
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def update(
        self, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        Обновить существующую сущность.

        Args:
            db_obj: Существующая сущность из БД
            obj_in: Pydantic схема или словарь с данными для обновления

        Returns:
            Обновленная сущность
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def delete(self, id: int) -> bool:
        """
        Удалить сущность по ID.

        Args:
            id: Идентификатор сущности

        Returns:
            True если удаление успешно, False если сущность не найдена
        """
        db_obj = await self.get(id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.commit()

        return True

    def _apply_filters(
        self, query: Select[tuple[ModelType]], filters: dict[str, Any]
    ) -> Select[tuple[ModelType]]:
        """
        Вспомогательный метод для применения фильтров к запросу.

        Args:
            query: SQLAlchemy запрос
            filters: Словарь фильтров

        Returns:
            Запрос с примененными фильтрами
        """
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        return query
