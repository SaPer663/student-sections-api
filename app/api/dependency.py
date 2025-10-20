from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.db.session import get_db
from app.models.user import User
from app.repositories import (
    RoleRepository,
    SectionRepository,
    StudentRepository,
    UserRepository,
)
from app.services import AuthService, SectionService, StudentService

security = HTTPBearer()


async def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    """
    Dependency для получения UserRepository.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


async def get_role_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> RoleRepository:
    """
    Dependency для получения RoleRepository.

    Args:
        db: Database session

    Returns:
        RoleRepository instance
    """
    return RoleRepository(db)


async def get_student_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> StudentRepository:
    """
    Dependency для получения StudentRepository.

    Args:
        db: Database session

    Returns:
        StudentRepository instance
    """
    return StudentRepository(db)


async def get_section_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> SectionRepository:
    """
    Dependency для получения SectionRepository.

    Args:
        db: Database session

    Returns:
        SectionRepository instance
    """
    return SectionRepository(db)


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
) -> AuthService:
    """
    Dependency для получения AuthService.

    Args:
        user_repo: User repository
        role_repo: Role repository

    Returns:
        AuthService instance
    """
    return AuthService(user_repo, role_repo)


async def get_student_service(
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
    section_repo: Annotated[SectionRepository, Depends(get_section_repository)],
) -> StudentService:
    """
    Dependency для получения StudentService.

    Args:
        student_repo: Student repository
        section_repo: Section repository

    Returns:
        StudentService instance
    """
    return StudentService(student_repo, section_repo)


async def get_section_service(
    section_repo: Annotated[SectionRepository, Depends(get_section_repository)]
) -> SectionService:
    """
    Dependency для получения SectionService.

    Args:
        section_repo: Section repository

    Returns:
        SectionService instance
    """
    return SectionService(section_repo)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Dependency для получения текущего аутентифицированного пользователя.

    Args:
        credentials: HTTP Authorization credentials с JWT токеном
        auth_service: Auth service

    Returns:
        Текущий пользователь

    Raises:
        HTTPException: Если токен невалиден или пользователь не найден
    """

    token = credentials.credentials
    return await auth_service.get_current_user(token)


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    Dependency для получения текущего активного пользователя.

    Args:
        current_user: Текущий пользователь

    Returns:
        Активный пользователь

    Raises:
        HTTPException: Если пользователь неактивен
    """
    if not current_user.is_active:
        raise UnauthorizedException(message="User account is deactivated")
    return current_user


def require_admin(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """
    Dependency для проверки что пользователь является администратором.

    Args:
        current_user: Текущий активный пользователь

    Returns:
        Пользователь с ролью admin

    Raises:
        HTTPException: Если пользователь не администратор
    """
    if not current_user.is_admin:
        raise UnauthorizedException(message="Only administrators can perform this action")
    return current_user


def require_user(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """
    Dependency для проверки что пользователь авторизован (любая роль).

    Args:
        current_user: Текущий активный пользователь

    Returns:
        Авторизованный пользователь
    """
    return current_user
