from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependency import get_current_active_user, get_section_service, require_admin
from app.models.user import User
from app.schemas import (
    PaginatedResponse,
    SectionCreate,
    SectionDetailResponse,
    SectionResponse,
    SectionUpdate,
    SortOrder,
)
from app.services.section_service import SectionService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SectionResponse],
    summary="Получить список секций",
    description="Получение списка секций с поддержкой пагинации, фильтрации и сортировки",
)
async def get_sections(
    section_service: Annotated[SectionService, Depends(get_section_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    offset: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество записей"),
    search: str | None = Query(None, description="Поиск по полям: name or description"),
    available_only: bool = Query(
        False, description="Показывать только секции со свободными местами"
    ),
    sort_by: str = Query("id", description="Поле для сортировки"),
    order: SortOrder = Query(SortOrder.ASC, description="Порядок сортировки"),
) -> PaginatedResponse[SectionResponse]:
    """
    Получить список секций.

    Доступно всем авторизованным пользователям.
    """

    return await section_service.get_sections(
        offset=offset,
        limit=limit,
        search=search,
        available_only=available_only,
        sort_by=sort_by,
        order=order.value,
    )


@router.get(
    "/{section_id}",
    response_model=SectionDetailResponse,
    summary="Получить секцию по ID",
    description="Получение детальной информации о секции со списком студентов и датами зачисления",
)
async def get_section(
    section_id: int,
    section_service: Annotated[SectionService, Depends(get_section_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> SectionDetailResponse:
    """
    Получить секцию по ID.

    Доступно всем авторизованным пользователям.
    """

    return await section_service.get_section_detail(section_id)


@router.post(
    "",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать секцию",
    description="Создание новой секции (только для администраторов)",
)
async def create_section(
    section_data: SectionCreate,
    section_service: Annotated[SectionService, Depends(get_section_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> SectionResponse:
    """
    Создать новую секцию.

    Требуется роль ADMIN.
    """

    return await section_service.create_section(section_data)


@router.put(
    "/{section_id}",
    response_model=SectionResponse,
    summary="Обновить секцию",
    description="Обновление данных секции (только для администраторов)",
)
async def update_section(
    section_id: int,
    section_data: SectionUpdate,
    section_service: Annotated[SectionService, Depends(get_section_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> SectionResponse:
    """
    Обновить данные секции.

    Требуется роль ADMIN.
    """

    return await section_service.update_section(section_id, section_data)


@router.delete(
    "/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить секцию",
    description="Удаление секции (только для администраторов)",
)
async def delete_section(
    section_id: int,
    section_service: Annotated[SectionService, Depends(get_section_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Удалить секцию.

    Требуется роль ADMIN.
    Секция должна быть пустой (без студентов).
    """

    await section_service.delete_section(section_id)
