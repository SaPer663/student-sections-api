from app.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories import RoleRepository, UserRepository
from app.schemas import LoginRequest, Token, UserCreate, UserCreateByAdmin, UserResponse


class AuthService:
    """Сервис для бизнес-логики авторизации и аутентификации."""

    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository) -> None:
        """
        Инициализация сервиса авторизации.

        Args:
            user_repository: Репозиторий для работы с пользователями
            role_repository: Репозиторий для работы с ролями
        """
        self.user_repo = user_repository
        self.role_repo = role_repository

    async def register(self, user_data: UserCreate) -> UserResponse:
        """
        Регистрация нового пользователя (только роль USER).

        Обычные пользователи могут регистрироваться самостоятельно,
        но только с ролью "user". Администраторов может создавать
        только существующий администратор.

        Args:
            user_data: Данные для создания пользователя

        Returns:
            Созданный пользователь

        Raises:
            AlreadyExistsException: Если пользователь с таким email уже существует
            ValidationException: Если роль "user" не найдена в системе
        """

        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise AlreadyExistsException(entity="User", field="email", value=user_data.email)

        user_role = await self.role_repo.get_user_role()
        if not user_role:
            raise ValidationException(
                "User role not found in the system. Please contact administrator."
            )

        hashed_password = get_password_hash(user_data.password)

        db_user = await self.user_repo.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role_id=user_role.id,
        )

        return UserResponse.model_validate(db_user)

    async def create_user_by_admin(
        self, user_data: UserCreateByAdmin, current_user: User
    ) -> UserResponse:
        """
        Создание пользователя администратором (с любой ролью).

        Только администратор может создавать пользователей с ролью "admin".

        Args:
            user_data: Данные для создания пользователя
            current_user: Текущий пользователь (должен быть админом)

        Returns:
            Созданный пользователь

        Raises:
            AlreadyExistsException: Если пользователь с таким email уже существует
            ValidationException: Если указанная роль не существует
            UnauthorizedException: Если текущий пользователь не админ
        """

        if not current_user.is_admin:
            raise UnauthorizedException("Only administrators can create users with specific roles")

        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise AlreadyExistsException(entity="User", field="email", value=user_data.email)

        role = await self.role_repo.get(user_data.role_id)
        if not role:
            raise ValidationException(f"Role with id {user_data.role_id} not found")

        hashed_password = get_password_hash(user_data.password)

        db_user = await self.user_repo.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role_id=user_data.role_id,
        )

        return UserResponse.model_validate(db_user)

    async def login(self, login_data: LoginRequest) -> Token:
        """
        Аутентификация пользователя и выдача JWT токена.

        Args:
            login_data: Email и пароль для входа

        Returns:
            JWT токен

        Raises:
            UnauthorizedException: Если учетные данные неверны
        """

        user = await self.user_repo.get_by_email(login_data.email)

        if not user:
            raise UnauthorizedException("Incorrect email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is deactivated")

        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.name, "role_id": user.role.id}
        )

        return Token(access_token=access_token, token_type="bearer")

    async def get_current_user(self, token: str) -> User:
        """
        Получить текущего пользователя по JWT токену.

        Args:
            token: JWT токен

        Returns:
            Пользователь

        Raises:
            UnauthorizedException: Если токен невалиден или пользователь не найден
        """

        payload = decode_access_token(token)

        if not payload:
            raise UnauthorizedException("Could not validate credentials")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Could not validate credentials")

        try:
            user_id = int(user_id_str)
        except ValueError:
            raise UnauthorizedException("Invalid token payload")

        user = await self.user_repo.get(user_id)

        if not user:
            raise NotFoundException("User", user_id)

        if not user.is_active:
            raise UnauthorizedException("User account is deactivated")

        return user

    async def refresh_token(self, token: str) -> Token:
        """
        Обновление JWT токена.

        Args:
            token: Текущий JWT токен

        Returns:
            Новый JWT токен

        Raises:
            UnauthorizedException: Если токен невалиден
        """
        user = await self.get_current_user(token)

        new_access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.name, "role_id": user.role.id}
        )

        return Token(access_token=new_access_token, token_type="bearer")

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Изменение пароля пользователя.

        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль

        Returns:
            True если пароль успешно изменен

        Raises:
            NotFoundException: Если пользователь не найден
            UnauthorizedException: Если старый пароль неверен
        """
        user = await self.user_repo.get(user_id)

        if not user:
            raise NotFoundException("User", user_id)

        if not verify_password(old_password, user.hashed_password):
            raise UnauthorizedException("Incorrect password")

        new_hashed_password = get_password_hash(new_password)

        user.hashed_password = new_hashed_password
        await self.user_repo.update(user, {"hashed_password": new_hashed_password})

        return True
