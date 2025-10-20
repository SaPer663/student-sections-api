from app.core.exceptions import AlreadyExistsException, NotFoundException, ValidationException
from app.repositories.section_repository import SectionRepository
from app.schemas import (
    PaginatedResponse,
    SectionCreate,
    SectionDetailResponse,
    SectionResponse,
    SectionUpdate,
    StudentInSectionInfo,
)


class SectionService:
    """Сервис для бизнес-логики работы с секциями."""

    def __init__(self, section_repo: SectionRepository) -> None:
        """
        Инициализация сервиса секций.

        Args:
            section_repo: Репозиторий секций
        """
        self.section_repo = section_repo

    async def create_section(self, section_data: SectionCreate) -> SectionResponse:
        """
        Создать новую секцию.

        Args:
            section_data: Данные для создания секции

        Returns:
            Созданная секция

        Raises:
            AlreadyExistsException: Если секция с таким названием уже существует
        """
        if await self.section_repo.exists_by_name(section_data.name):
            raise AlreadyExistsException(entity="Section", field="name", value=section_data.name)

        section = await self.section_repo.create(section_data)

        section._current_enrollment = 0
        return SectionResponse.model_validate(section)

    async def get_section(self, section_id: int) -> SectionResponse:
        """
        Получить секцию по ID.

        Args:
            section_id: ID секции

        Returns:
            Данные секции

        Raises:
            NotFoundException: Если секция не найдена
        """
        section = await self.section_repo.get(section_id)
        if not section:
            raise NotFoundException("Section", section_id)

        student_count = await self.section_repo.get_student_count(section_id)
        section._current_enrollment = student_count

        return SectionResponse.model_validate(section)

    async def get_section_detail(self, section_id: int) -> SectionDetailResponse:
        """
        Получить детальную информацию о секции со списком студентов.

        Args:
            section_id: ID секции

        Returns:
            Детальная информация о секции

        Raises:
            NotFoundException: Если секция не найдена
        """
        section = await self.section_repo.get_with_students(section_id)
        if not section:
            raise NotFoundException("Section", section_id)

        students_info = [
            StudentInSectionInfo(
                student_id=student.student_id,
                first_name=student.student.first_name,
                last_name=student.student.last_name,
                email=student.student.email,
                enrollment_date=student.enrollment_date,
            )
            for student in section.students
        ]

        student_count = len(section.students)
        section._current_enrollment = student_count

        section_dict = SectionResponse.model_validate(section).model_dump()
        section_dict["students"] = students_info

        return SectionDetailResponse(**section_dict)

    async def get_sections(
        self,
        offset: int = 0,
        limit: int = 10,
        search: str | None = None,
        available_only: bool = False,
        sort_by: str = "id",
        order: str = "asc",
    ) -> PaginatedResponse[SectionResponse]:
        """
        Получить список секций с фильтрацией и пагинацией.

        Args:
            offset: Количество записей для пропуска
            limit: Максимальное количество записей
            search: Поисковый запрос
            available_only: Показывать только секции со свободными местами
            sort_by: Поле для сортировки
            order: Порядок сортировки

        Returns:
            Пагинированный список секций
        """
        if search:
            sections = await self.section_repo.search(search, offset, limit)
            total = await self.section_repo.count_search(search)
        elif available_only:
            sections = await self.section_repo.get_available_sections(offset, limit)
            total = await self.section_repo.count_available()
        else:
            sections = await self.section_repo.get_multi(
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                order=order,
            )
            total = await self.section_repo.count()

        items = []
        for section in sections:
            student_count = await self.section_repo.get_student_count(section.id)

            section._current_enrollment = student_count
            items.append(SectionResponse.model_validate(section))

        return PaginatedResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def update_section(
        self,
        section_id: int,
        section_data: SectionUpdate,
    ) -> SectionResponse:
        """
        Обновить данные секции.

        Args:
            section_id: ID секции
            section_data: Данные для обновления

        Returns:
            Обновленная секция

        Raises:
            NotFoundException: Если секция не найдена
            AlreadyExistsException: Если название уже занято другой секцией
            ValidationException: Если новая вместимость меньше текущего количества студентов
        """
        section = await self.section_repo.get(section_id)
        if not section:
            raise NotFoundException("Section", section_id)

        if section_data.name and section_data.name != section.name:
            if await self.section_repo.exists_by_name(section_data.name):
                raise AlreadyExistsException(
                    entity="Section", field="name", value=section_data.name
                )

        if section_data.max_capacity is not None:
            current_enrollment = await self.section_repo.get_student_count(section_id)
            if section_data.max_capacity < current_enrollment:
                raise ValidationException(
                    f"Cannot set max_capacity to {section_data.max_capacity}. "
                    f"Current enrollment is {current_enrollment}"
                )

        updated_section = await self.section_repo.update(section, section_data)

        student_count = await self.section_repo.get_student_count(section_id)
        updated_section._current_enrollment = student_count
        return SectionResponse.model_validate(updated_section)

    async def delete_section(self, section_id: int) -> bool:
        """
        Удалить секцию.

        Args:
            section_id: ID секции

        Returns:
            True если удаление успешно

        Raises:
            NotFoundException: Если секция не найдена
            ValidationException: Если в секции есть студенты
        """
        section = await self.section_repo.get(section_id)
        if not section:
            raise NotFoundException("Section", section_id)

        student_count = await self.section_repo.get_student_count(section_id)
        if student_count > 0:
            raise ValidationException(
                f"Cannot delete section '{section.name}'. "
                f"It has {student_count} enrolled students. "
                "Please unenroll all students first."
            )

        return await self.section_repo.delete(section_id)
