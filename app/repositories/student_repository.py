from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student
from app.models.student_section import StudentSection
from app.repositories.base import BaseRepository
from app.schemas.student import StudentCreate, StudentUpdate


class StudentRepository(BaseRepository[Student, StudentCreate, StudentUpdate]):
    """Репозиторий для работы со студентами."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Инициализация репозитория студентов.

        Args:
            db: Асинхронная сессия БД
        """
        super().__init__(Student, db)

    async def get_by_email(self, email: str) -> Student | None:
        """
        Получить студента по email.

        Args:
            email: Email студента

        Returns:
            Найденный студент или None
        """
        result = await self.db.execute(select(Student).where(Student.email == email))
        return result.scalar_one_or_none()

    async def get_with_sections(self, student_id: int) -> Student | None:
        """
        Получить студента со списком его секций.

        Args:
            student_id: ID студента

        Returns:
            Студент с загруженными секциями или None
        """
        result = await self.db.execute(
            select(Student)
            .where(Student.id == student_id)
            .options(selectinload(Student.sections).selectinload(StudentSection.section))
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        search_query: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Student]:
        """
        Поиск студентов по имени или email.

        Args:
            search_query: Поисковый запрос
            offset: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список найденных студентов
        """
        search_pattern = f"%{search_query}%"

        result = await self.db.execute(
            select(Student)
            .where(
                or_(
                    Student.first_name.ilike(search_pattern),
                    Student.last_name.ilike(search_pattern),
                    Student.email.ilike(search_pattern),
                )
            )
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_section(
        self,
        section_id: int,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Student]:
        """
        Получить студентов, записанных в определенную секцию.

        Args:
            section_id: ID секции
            offset: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список студентов в секции
        """
        result = await self.db.execute(
            select(Student)
            .join(StudentSection)
            .where(StudentSection.section_id == section_id)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def exists_by_email(self, email: str) -> bool:
        """
        Проверить существование студента с указанным email.

        Args:
            email: Email для проверки

        Returns:
            True если студент существует, иначе False
        """
        student = await self.get_by_email(email)
        return student is not None

    async def is_enrolled_in_section(
        self,
        student_id: int,
        section_id: int,
    ) -> bool:
        """
        Проверить, записан ли студент в секцию.

        Args:
            student_id: ID студента
            section_id: ID секции

        Returns:
            True если студент записан в секцию
        """
        result = await self.db.execute(
            select(StudentSection).where(
                StudentSection.student_id == student_id,
                StudentSection.section_id == section_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def enroll_in_section(
        self,
        student_id: int,
        section_id: int,
        enrollment_date: date,
    ) -> StudentSection:
        """
        Записать студента в секцию.

        Args:
            student_id: ID студента
            section_id: ID секции
            enrollment_date: Дата зачисления

        Returns:
            Созданная запись StudentSection
        """
        student_section = StudentSection(
            student_id=student_id,
            section_id=section_id,
            enrollment_date=enrollment_date,
        )

        self.db.add(student_section)
        await self.db.commit()
        await self.db.refresh(student_section)

        return student_section

    async def unenroll_from_section(
        self,
        student_id: int,
        section_id: int,
    ) -> bool:
        """
        Отчислить студента из секции.

        Args:
            student_id: ID студента
            section_id: ID секции

        Returns:
            True если успешно отчислен, False если не был записан
        """
        result = await self.db.execute(
            select(StudentSection).where(
                StudentSection.student_id == student_id,
                StudentSection.section_id == section_id,
            )
        )
        student_section = result.scalar_one_or_none()

        if not student_section:
            return False

        await self.db.delete(student_section)
        await self.db.commit()

        return True

    async def count_search(self, search_query: str) -> int:
        """
        Подсчет студентов по поисковому запросу.

        Args:
            search_query: Поисковый запрос

        Returns:
            Количество найденных студентов
        """
        search_pattern = f"%{search_query}%"

        result = await self.db.execute(
            select(func.count())
            .select_from(Student)
            .where(
                or_(
                    Student.first_name.ilike(search_pattern),
                    Student.last_name.ilike(search_pattern),
                    Student.email.ilike(search_pattern),
                )
            )
        )
        return result.scalar_one()
