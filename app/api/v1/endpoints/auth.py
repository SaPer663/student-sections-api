from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependency import get_auth_service, get_current_user, require_admin
from app.core.exceptions import (
    AlreadyExistsException,
    AppException,
    UnauthorizedException,
)
from app.models.user import User
from app.schemas import LoginRequest, Token, UserCreate, UserCreateByAdmin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создание нового пользователя с ролью 'user'. Доступно без авторизации.",
)
async def register(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """
    Регистрация нового пользователя.

    Любой желающий может зарегистрироваться как обычный пользователь (роль 'user').
    Администраторов могут создавать только существующие администраторы.

    Args:
        user_data: Данные для регистрации (email, password, full_name)
        auth_service: Сервис авторизации

    Returns:
        Данные созданного пользователя

    Raises:
        HTTPException 409: Если пользователь с таким email уже существует
        HTTPException 422: Если данные не прошли валидацию
    """
    try:
        user = await auth_service.register(user_data)
        return user
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )


@router.post(
    "/admin/create-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание пользователя администратором",
    description="Создание пользователя с любой ролью (только для администраторов)",
)
async def create_user_by_admin(
    user_data: UserCreateByAdmin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(require_admin)],
) -> UserResponse:
    """
    Создание пользователя администратором.

    Только администраторы могут создавать других пользователей, включая администраторов.

    Args:
        user_data: Данные для создания пользователя (email, password, full_name, role_id)
        auth_service: Сервис авторизации
        current_user: Текущий пользователь (должен быть админом)

    Returns:
        Данные созданного пользователя

    Raises:
        HTTPException 403: Если текущий пользователь не администратор
        HTTPException 409: Если пользователь с таким email уже существует
        HTTPException 422: Если данные не прошли валидацию
    """
    try:
        user = await auth_service.create_user_by_admin(user_data, current_user)
        return user
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему",
    description="Аутентификация пользователя и получение JWT токена",
)
async def login(
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """
    Аутентификация пользователя.

    Args:
        login_data: Email и пароль для входа
        auth_service: Сервис авторизации

    Returns:
        JWT токен для доступа к защищенным endpoints

    Raises:
        HTTPException 401: Если учетные данные неверны
    """
    try:
        token = await auth_service.login(login_data)
        return token
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить текущего пользователя",
    description="Получение информации о текущем аутентифицированном пользователе",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """
    Получить информацию о текущем пользователе.

    Args:
        current_user: Текущий аутентифицированный пользователь

    Returns:
        Данные текущего пользователя

    Raises:
        HTTPException 401: Если токен невалиден
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Обновить токен",
    description="Получение нового JWT токена на основе текущего",
)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """
    Обновить JWT токен.

    Args:
        current_user: Текущий аутентифицированный пользователь
        auth_service: Сервис авторизации

    Returns:
        Новый JWT токен

    Raises:
        HTTPException 401: Если токен невалиден
    """
    try:
        from app.core.security import create_access_token

        new_token = create_access_token(
            data={
                "sub": str(current_user.id),
                "role": current_user.role.name,
                "role_id": current_user.role.id,
            }
        )
        return Token(access_token=new_token, token_type="bearer")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
