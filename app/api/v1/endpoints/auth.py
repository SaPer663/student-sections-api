from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependency import get_auth_service, get_current_user, require_admin
from app.core.exceptions import AppException
from app.core.security import create_access_token
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
        AlreadyExistsException 409: Если пользователь с таким email уже существует
        AppException 422: Если данные не прошли валидацию
    """

    return await auth_service.register(user_data)


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
        UnauthorizedException 403: Если текущий пользователь не администратор
        AlreadyExistsException 409: Если пользователь с таким email уже существует
        AppException 422: Если данные не прошли валидацию
    """

    return await auth_service.create_user_by_admin(user_data, current_user)


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
        UnauthorizedException 401: Если учетные данные неверны
        AppException 422: Если данные не прошли валидацию
    """

    return await auth_service.login(login_data)


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
        AppException : Если токен невалиден
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

        new_token = create_access_token(
            data={
                "sub": str(current_user.id),
                "role": current_user.role.name,
                "role_id": current_user.role.id,
            }
        )
        return Token(access_token=new_token, token_type="bearer")
    except Exception:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Could not refresh token",
            detail={"WWW-Authenticate": "Bearer"},
        )
