from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.base import BaseRepository
from app.schemas.role import RoleCreate, RoleUpdate


class RoleRepository(BaseRepository[Role, RoleCreate, RoleUpdate]):
    """Репозиторий для работы с ролями."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Инициализация репозитория ролей.

        Args:
            db: Асинхронная сессия БД
        """
        super().__init__(Role, db)

    async def get_by_name(self, name: str) -> Role | None:
        """
        Получить роль по имени.

        Args:
            name: Название роли

        Returns:
            Найденная роль или None
        """
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def exists_by_name(self, name: str) -> bool:
        """
        Проверить существование роли с указанным именем.

        Args:
            name: Название для проверки

        Returns:
            True если роль существует, иначе False
        """
        role = await self.get_by_name(name)
        return role is not None

    async def get_admin_role(self) -> Role | None:
        """
        Получить роль администратора.

        Returns:
            Роль admin или None
        """
        return await self.get_by_name("admin")

    async def get_user_role(self) -> Role | None:
        """
        Получить роль обычного пользователя.

        Returns:
            Роль user или None
        """
        return await self.get_by_name("user")
