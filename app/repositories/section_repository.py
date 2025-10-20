from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.section import Section
from app.models.student_section import StudentSection
from app.repositories.base import BaseRepository
from app.schemas.section import SectionCreate, SectionUpdate


class SectionRepository(BaseRepository[Section, SectionCreate, SectionUpdate]):
    """Репозиторий для работы с секциями."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Инициализация репозитория секций.

        Args:
            db: Асинхронная сессия БД
        """
        super().__init__(Section, db)

    async def get_by_name(self, name: str) -> Section | None:
        """
        Получить секцию по названию.

        Args:
            name: Название секции

        Returns:
            Найденная секция или None
        """
        result = await self.db.execute(select(Section).where(Section.name == name))
        return result.scalar_one_or_none()

    async def get_with_students(self, section_id: int) -> Section | None:
        """
        Получить секцию со списком студентов.

        Args:
            section_id: ID секции

        Returns:
            Секция с загруженными студентами или None
        """
        result = await self.db.execute(
            select(Section)
            .where(Section.id == section_id)
            .options(selectinload(Section.students).selectinload(StudentSection.student))
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        search_query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Section]:
        """
        Поиск секций по названию или описанию.

        Args:
            search_query: Поисковый запрос
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список найденных секций
        """
        search_pattern = f"%{search_query}%"

        result = await self.db.execute(
            select(Section)
            .where(
                or_(
                    Section.name.ilike(search_pattern),
                    Section.description.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_available_sections(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Section]:
        """
        Получить секции со свободными местами.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список секций с доступными местами
        """
        subquery = (
            select(
                StudentSection.section_id,
                func.count(StudentSection.student_id).label("student_count"),
            )
            .group_by(StudentSection.section_id)
            .subquery()
        )

        result = await self.db.execute(
            select(Section)
            .outerjoin(subquery, Section.id == subquery.c.section_id)
            .where(
                or_(
                    subquery.c.student_count < Section.max_capacity,
                    subquery.c.student_count.is_(None),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def exists_by_name(self, name: str) -> bool:
        """
        Проверить существование секции с указанным названием.

        Args:
            name: Название для проверки

        Returns:
            True если секция существует, иначе False
        """
        section = await self.get_by_name(name)
        return section is not None

    async def get_student_count(self, section_id: int) -> int:
        """
        Получить количество студентов в секции.

        Args:
            section_id: ID секции

        Returns:
            Количество студентов
        """
        result = await self.db.execute(
            select(func.count())
            .select_from(StudentSection)
            .where(StudentSection.section_id == section_id)
        )
        return result.scalar_one()

    async def is_full(self, section_id: int, max_capacity: int) -> bool:
        """
        Проверить, заполнена ли секция.

        Args:
            section_id: ID секции

        Returns:
            True если секция заполнена
        """

        student_count = await self.get_student_count(section_id)

        return student_count >= max_capacity

    async def count_search(self, search_query: str) -> int:
        """
        Подсчет секций по поисковому запросу.

        Args:
            search_query: Поисковый запрос

        Returns:
            Количество найденных секций
        """
        search_pattern = f"%{search_query}%"

        result = await self.db.execute(
            select(func.count())
            .select_from(Section)
            .where(
                or_(
                    Section.name.ilike(search_pattern),
                    Section.description.ilike(search_pattern),
                )
            )
        )
        return result.scalar_one()

    async def count_available(self) -> int:
        """
        Подсчет секций со свободными местами.

        Returns:
            Количество секций с доступными местами
        """
        subquery = (
            select(
                StudentSection.section_id,
                func.count(StudentSection.student_id).label("student_count"),
            )
            .group_by(StudentSection.section_id)
            .subquery()
        )

        result = await self.db.execute(
            select(func.count())
            .select_from(Section)
            .outerjoin(subquery, Section.id == subquery.c.section_id)
            .where(
                or_(
                    subquery.c.student_count < Section.max_capacity,
                    subquery.c.student_count.is_(None),
                )
            )
        )
        return result.scalar_one()
