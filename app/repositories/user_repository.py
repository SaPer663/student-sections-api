from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Репозиторий для работы с пользователями."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Инициализация репозитория пользователей.

        Args:
            db: Асинхронная сессия БД
        """
        super().__init__(User, db)

    async def create_user(
        self, email: str, hashed_password: str, full_name: str, role_id: int
    ) -> User:
        """
        Создать нового пользователя с хешированным паролем.

        Args:
            email: Email пользователя
            hashed_password: Хешированный пароль
            full_name: Полное имя
            role_id: ID роли пользователя

        Returns:
            Созданный пользователь
        """
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role_id=role_id,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user, ["role"])

        return db_user

    async def get_by_email(self, email: str) -> User | None:
        """
        Получить пользователя по email с загруженной ролью.

        Args:
            email: Email пользователя

        Returns:
            Найденный пользователь или None
        """
        result = await self.db.execute(
            select(User).where(User.email == email).options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get(self, id: int) -> User | None:
        """
        Получить пользователя по ID с загруженной ролью.

        Args:
            id: ID пользователя

        Returns:
            Найденный пользователь или None
        """
        result = await self.db.execute(
            select(User).where(User.id == id).options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get_active_users(self, offset: int = 0, limit: int = 100) -> list[User]:
        """
        Получить список активных пользователей.

        Args:
            offset: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список активных пользователей
        """
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)  # noqa: E712
            .options(selectinload(User.role))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def exists_by_email(self, email: str) -> bool:
        """
        Проверить существование пользователя с указанным email.

        Args:
            email: Email для проверки

        Returns:
            True если пользователь существует, иначе False
        """
        user = await self.get_by_email(email)
        return user is not None

    async def deactivate(self, user_id: int) -> User | None:
        """
        Деактивировать пользователя (soft delete).

        Args:
            user_id: ID пользователя

        Returns:
            Деактивированный пользователь или None если не найден
        """
        user = await self.get(user_id)
        if not user:
            return None

        user.is_active = False
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user, ["role"])

        return user

    async def activate(self, user_id: int) -> User | None:
        """
        Активировать пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Активированный пользователь или None если не найден
        """
        user = await self.get(user_id)
        if not user:
            return None

        user.is_active = True
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user, ["role"])

        return user
