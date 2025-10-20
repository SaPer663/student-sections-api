from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependency import (
    get_current_active_user,
    get_student_service,
    require_admin,
)
from app.models.user import User
from app.schemas import (
    EnrollmentRequest,
    PaginatedResponse,
    SortOrder,
    StudentCreate,
    StudentDetailResponse,
    StudentResponse,
    StudentSectionInfo,
    StudentUpdate,
)
from app.services.student_service import StudentService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[StudentResponse],
    summary="Получить список студентов",
    description="Получение списка студентов с поддержкой пагинации, фильтрации и сортировки",
)
async def get_students(
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    offset: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество записей"),
    search: str | None = Query(None, description="Поиск по полям: name or email"),
    section_id: int | None = Query(None, description="Фильтер по ID секции"),
    sort_by: str = Query("id", description="Поле для сортировки"),
    order: SortOrder = Query(SortOrder.ASC, description="Порядок сортировки"),
) -> PaginatedResponse[StudentResponse]:
    """
    Получить список студентов.

    Доступно всем авторизованным пользователям.
    """

    return await student_service.get_students(
        offset=offset,
        limit=limit,
        search=search,
        section_id=section_id,
        sort_by=sort_by,
        order=order.value,
    )


@router.get(
    "/{student_id}",
    response_model=StudentDetailResponse,
    summary="Получить студента по ID",
    description="Получение детальной информации о студенте со списком секций",
)
async def get_student(
    student_id: int,
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StudentDetailResponse:
    """
    Получить студента по ID.

    Доступно всем авторизованным пользователям.
    """

    return await student_service.get_student_detail(student_id)


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать студента",
    description="Создание нового студента (только для администраторов)",
)
async def create_student(
    student_data: StudentCreate,
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> StudentResponse:
    """
    Создать нового студента.

    Требуется роль ADMIN.
    """

    return await student_service.create_student(student_data)


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Обновить студента",
    description="Обновление данных студента (только для администраторов)",
)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> StudentResponse:
    """
    Обновить данные студента.

    Требуется роль ADMIN.
    """

    return await student_service.update_student(student_id, student_data)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить студента",
    description="Удаление студента (только для администраторов)",
)
async def delete_student(
    student_id: int,
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Удалить студента.

    Требуется роль ADMIN.
    """

    await student_service.delete_student(student_id)


@router.post(
    "/{student_id}/sections/{section_id}",
    response_model=StudentSectionInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Записать студента в секцию",
    description="Запись студента в секцию с указанием даты зачисления (только для администраторов)",
)
async def enroll_student_in_section(
    student_id: int,
    section_id: int,
    enrollment_data: EnrollmentRequest,
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> StudentSectionInfo:
    """
    Записать студента в секцию.

    Требуется роль ADMIN.
    """

    return await student_service.enroll_student_in_section(
        student_id=student_id,
        section_id=section_id,
        enrollment_date=enrollment_data.enrollment_date,
    )


@router.delete(
    "/{student_id}/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отчислить студента из секции",
    description="Отчисление студента из секции (только для администраторов)",
)
async def unenroll_student_from_section(
    student_id: int,
    section_id: int,
    student_service: Annotated[StudentService, Depends(get_student_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Отчислить студента из секции.

    Требуется роль ADMIN.
    """

    await student_service.unenroll_student_from_section(student_id, section_id)
