from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Role, User


async def init_roles(db: AsyncSession) -> dict[str, Role]:
    """
    Инициализация ролей.

    Args:
        db: Асинхронная сессия БД

    Returns:
        Словарь с ролями {name: Role}
    """
    roles_data = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "user", "description": "Regular user with limited access"},
    ]

    roles = {}

    for role_data in roles_data:

        result = await db.execute(select(Role).where(Role.name == role_data["name"]))
        role = result.scalar_one_or_none()

        if not role:

            role = Role(**role_data)
            db.add(role)
            await db.commit()
            await db.refresh(role)
            print(f"Created role: {role.name}")
        else:
            print(f"ℹRole already exists: {role.name}")

        roles[role.name] = role

    return roles


async def init_admin(db: AsyncSession, admin_role: Role) -> User | None:
    """
    Инициализация первого администратора.

    Args:
        db: Асинхронная сессия БД
        admin_role: Роль администратора

    Returns:
        Созданный или существующий пользователь-администратор
    """
    admin_email = settings.initial_admin.ADMIN_EMAIL

    result = await db.execute(select(User).where(User.email == admin_email))
    admin = result.scalar_one_or_none()

    if not admin:
        hashed_password = get_password_hash(settings.initial_admin.ADMIN_PASSWORD)

        admin = User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name=settings.initial_admin.ADMIN_FULL_NAME,
            role_id=admin_role.id,
            is_active=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print(f"Created initial admin user: {admin.email}")
        print(f"   Password: {settings.initial_admin.ADMIN_PASSWORD}")
        print("    Please change the password after first login!")
    else:
        print(f"Admin user already exists: {admin.email}")

    return admin


async def initialize_database(db: AsyncSession) -> None:
    """
    Полная инициализация базы данных с начальными данными.

    Args:
        db: Асинхронная сессия БД
    """
    print("\n" + "=" * 50)
    print("Starting database initialization...")
    print("=" * 50 + "\n")

    try:
        # Инициализируем роли
        print("Initializing roles...")
        roles = await init_roles(db)

        # Инициализируем первого админа
        print("\nInitializing admin user...")
        await init_admin(db, roles["admin"])

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"\nError during database initialization: {e}")
        await db.rollback()
        raise
