import datetime

from app.core.exceptions import AlreadyExistsException, NotFoundException, ValidationException
from app.repositories import SectionRepository, StudentRepository
from app.schemas import (
    PaginatedResponse,
    StudentCreate,
    StudentDetailResponse,
    StudentResponse,
    StudentSectionInfo,
    StudentUpdate,
)


class StudentService:
    """Сервис для бизнес-логики работы со студентами."""

    def __init__(
        self,
        student_repo: StudentRepository,
        section_repo: SectionRepository,
    ) -> None:
        """
        Инициализация сервиса студентов.

        Args:
            student_repo: Репозиторий студентов
            section_repo: Репозиторий секций
        """
        self.student_repo = student_repo
        self.section_repo = section_repo

    async def create_student(self, student_data: StudentCreate) -> StudentResponse:
        """
        Создать нового студента.

        Args:
            student_data: Данные для создания студента

        Returns:
            Созданный студент

        Raises:
            AlreadyExistsException: Если студент с таким email уже существует
        """

        if await self.student_repo.exists_by_email(student_data.email):
            raise AlreadyExistsException(entity="Student", field="email", value=student_data.email)

        student = await self.student_repo.create(student_data)
        return StudentResponse.model_validate(student)

    async def get_student(self, student_id: int) -> StudentResponse:
        """
        Получить студента по ID.

        Args:
            student_id: ID студента

        Returns:
            Данные студента

        Raises:
            NotFoundException: Если студент не найден
        """
        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException("Student", student_id)

        return StudentResponse.model_validate(student)

    async def get_student_detail(self, student_id: int) -> StudentDetailResponse:
        """
        Получить детальную информацию о студенте со списком секций.

        Args:
            student_id: ID студента

        Returns:
            Детальная информация о студенте

        Raises:
            NotFoundException: Если студент не найден
        """
        student = await self.student_repo.get_with_sections(student_id)
        if not student:
            raise NotFoundException("Student", student_id)

        sections_info = [
            StudentSectionInfo(
                section_id=section.section_id,
                section_name=section.section.name,
                enrollment_date=section.enrollment_date,
            )
            for section in student.sections
        ]

        student_dict = StudentResponse.model_validate(student).model_dump()
        student_dict["sections"] = sections_info

        return StudentDetailResponse(**student_dict)

    async def get_students(
        self,
        offset: int = 0,
        limit: int = 10,
        search: str | None = None,
        section_id: int | None = None,
        sort_by: str = "id",
        order: str = "asc",
    ) -> PaginatedResponse[StudentResponse]:
        """
        Получить список студентов с фильтрацией и пагинацией.

        Args:
            offset: Количество записей для пропуска
            limit: Максимальное количество записей
            search: Поисковый запрос
            section_id: Фильтр по секции
            sort_by: Поле для сортировки
            order: Порядок сортировки

        Returns:
            Пагинированный список студентов
        """

        if search:
            students = await self.student_repo.search(search, offset, limit)
            total = await self.student_repo.count_search(search)
        elif section_id:
            students = await self.student_repo.get_by_section(section_id, offset, limit)
            total = await self.section_repo.get_student_count(section_id)
        else:
            students = await self.student_repo.get_multi(
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                order=order,
            )
            total = await self.student_repo.count()

        items = [StudentResponse.model_validate(s) for s in students]

        return PaginatedResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def update_student(
        self,
        student_id: int,
        student_data: StudentUpdate,
    ) -> StudentResponse:
        """
        Обновить данные студента.

        Args:
            student_id: ID студента
            student_data: Данные для обновления

        Returns:
            Обновленный студент

        Raises:
            NotFoundException: Если студент не найден
            AlreadyExistsException: Если email уже занят другим студентом
        """
        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException("Student", student_id)

        if student_data.email and student_data.email != student.email:
            if await self.student_repo.exists_by_email(student_data.email):
                raise AlreadyExistsException(
                    entity="Student", field="email", value=student_data.email
                )

        updated_student = await self.student_repo.update(student, student_data)
        return StudentResponse.model_validate(updated_student)

    async def delete_student(self, student_id: int) -> bool:
        """
        Удалить студента.

        Args:
            student_id: ID студента

        Returns:
            True если удаление успешно

        Raises:
            NotFoundException: Если студент не найден
        """
        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException("Student", student_id)

        return await self.student_repo.delete(student_id)

    async def enroll_student_in_section(
        self,
        student_id: int,
        section_id: int,
        enrollment_date: datetime.date,
    ) -> StudentSectionInfo:
        """
        Записать студента в секцию.

        Args:
            student_id: ID студента
            section_id: ID секции
            enrollment_date: Дата зачисления

        Returns:
            Информация о записи

        Raises:
            NotFoundException: Если студент или секция не найдены
            ValidationException: Если студент уже записан или секция заполнена
        """

        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException("Student", student_id)

        section = await self.section_repo.get(section_id)
        if not section:
            raise NotFoundException("Section", section_id)

        if await self.student_repo.is_enrolled_in_section(student_id, section_id):
            raise ValidationException(
                f"Student {student_id} is already enrolled in section {section_id}"
            )

        if await self.section_repo.is_full(
            section_id=section_id, max_capacity=section.max_capacity
        ):
            raise ValidationException(
                f"Section '{section.name}' is full (capacity: {section.max_capacity})"
            )

        await self.student_repo.enroll_in_section(
            student_id,
            section_id,
            enrollment_date,
        )

        return StudentSectionInfo(
            section_id=section_id,
            section_name=section.name,
            enrollment_date=enrollment_date,
        )

    async def unenroll_student_from_section(
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
            True если отчисление успешно

        Raises:
            NotFoundException: Если студент или секция не найдены
            ValidationException: Если студент не записан в секцию
        """
        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException("Student", student_id)

        section = await self.section_repo.get(section_id)
        if not section:
            raise NotFoundException("Section", section_id)

        if not await self.student_repo.is_enrolled_in_section(student_id, section_id):
            raise ValidationException(
                f"Student {student_id} is not enrolled in section {section_id}"
            )

        return await self.student_repo.unenroll_from_section(student_id, section_id)
