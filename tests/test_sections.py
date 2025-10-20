import datetime
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from polyfactory.factories.pydantic_factory import ModelFactory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models import Base, Role, Section, Student, StudentSection, User
from app.schemas.section import SectionCreate, SectionUpdate


class SectionFactory(ModelFactory[SectionCreate]):
    """Фабрика для генерации данных секций."""

    __model__ = SectionCreate
    __check_model__ = False

    @classmethod
    def name(cls) -> str:
        """Генерация уникального названия секции."""
        return f"Test Section {cls.__random__.randint(1000, 9999)}"

    @classmethod
    def description(cls) -> str:
        """Генерация описания секции."""
        return f"Description for test section {cls.__random__.randint(1000, 9999)}"

    @classmethod
    def max_capacity(cls) -> int:
        """Генерация вместимости секции."""
        return cls.__random__.randint(15, 30)


class SectionUpdateFactory(ModelFactory[SectionUpdate]):
    """Фабрика для генерации данных обновления секций."""

    __model__ = SectionUpdate
    __check_model__ = False

    @classmethod
    def name(cls) -> str | None:
        """Генерация названия для обновления."""
        return f"Updated Section {cls.__random__.randint(1000, 9999)}"

    @classmethod
    def description(cls) -> str | None:
        """Генерация описания для обновления."""
        return f"Updated description {cls.__random__.randint(1000, 9999)}"

    @classmethod
    def max_capacity(cls) -> int | None:
        """Генерация новой вместимости."""
        return cls.__random__.randint(20, 40)


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession]:
    """
    Создание тестовой базы данных для каждого теста.

    Использует SQLite в памяти для быстрого выполнения тестов.
    """

    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """HTTP клиент для тестирования API с подменой database dependency."""
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_role(test_db: AsyncSession) -> Role:
    """Создание роли администратора."""
    role = Role(name="admin", description="Administrator role")
    test_db.add(role)
    await test_db.commit()
    await test_db.refresh(role)
    return role


@pytest.fixture
async def user_role(test_db: AsyncSession) -> Role:
    """Создание роли пользователя."""
    role = Role(name="user", description="User role")
    test_db.add(role)
    await test_db.commit()
    await test_db.refresh(role)
    return role


@pytest.fixture
async def admin_user(test_db: AsyncSession, admin_role: Role) -> User:
    """Создание тестового администратора."""
    user = User(
        email="admin@test.com",
        hashed_password="hashed_password",
        full_name="Admin User",
        role_id=admin_role.id,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user, ["role"])
    return user


@pytest.fixture
async def regular_user(test_db: AsyncSession, user_role: Role) -> User:
    """Создание тестового обычного пользователя."""
    user = User(
        email="user@test.com",
        hashed_password="hashed_password",
        full_name="Regular User",
        role_id=user_role.id,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user, ["role"])
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """JWT токен для администратора."""
    return create_access_token(
        data={
            "sub": str(admin_user.id),
            "role": admin_user.role.name,
            "role_id": admin_user.role.id
        }
    )


@pytest.fixture
def user_token(regular_user: User) -> str:
    """JWT токен для обычного пользователя."""
    return create_access_token(
        data={
            "sub": str(regular_user.id),
            "role": regular_user.role.name,
            "role_id": regular_user.role.id
        }
    )


@pytest.fixture
async def test_section(test_db: AsyncSession) -> Section:
    """Создание тестовой секции."""
    section = Section(
        name="Test Programming Section",
        description="Test programming course",
        max_capacity=20,
    )
    test_db.add(section)
    await test_db.commit()
    await test_db.refresh(section)
    return section


@pytest.fixture
async def test_sections(test_db: AsyncSession) -> list[Section]:
    """Создание нескольких тестовых секций."""
    sections = [
        Section(
            name=f"Section {i}",
            description=f"Description {i}",
            max_capacity=20 + i,
        )
        for i in range(1, 6)
    ]

    for section in sections:
        test_db.add(section)

    await test_db.commit()

    for section in sections:
        await test_db.refresh(section)

    return sections


@pytest.fixture
async def test_student(test_db: AsyncSession) -> Student:
    """Создание тестового студента."""
    student = Student(
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        date_of_birth=datetime.date(2000, 1, 1),
    )
    test_db.add(student)
    await test_db.commit()
    await test_db.refresh(student)
    return student


@pytest.fixture
async def section_with_students(test_db: AsyncSession, test_section: Section) -> Section:
    """Секция с записанными студентами."""
    students = [
        Student(
            first_name=f"Student{i}",
            last_name=f"Last{i}",
            email=f"student{i}@test.com",
            date_of_birth=datetime.date(2000 + i, 1, 1),
        )
        for i in range(1, 4)
    ]

    for student in students:
        test_db.add(student)

    await test_db.commit()

    for student in students:
        await test_db.refresh(student)

        enrollment = StudentSection(
            student_id=student.id,
            section_id=test_section.id,
            enrollment_date=datetime.date.today(),
        )
        test_db.add(enrollment)

    await test_db.commit()
    await test_db.refresh(test_section)

    return test_section


@pytest.mark.asyncio
async def test_get_sections_success(
    test_client: AsyncClient, user_token: str, test_sections: list[Section]
):
    """Тест успешного получения списка секций."""
    response = await test_client.get(
        "/api/v1/sections", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == len(test_sections)
    assert len(data["items"]) == len(test_sections)


@pytest.mark.asyncio
async def test_get_sections_pagination(
    test_client: AsyncClient, user_token: str, test_sections: list[Section]
):
    """Тест пагинации при получении секций."""
    response = await test_client.get(
        "/api/v1/sections?offset=0&limit=2", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == len(test_sections)
    assert data["offset"] == 0
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_get_sections_search(
    test_client: AsyncClient, user_token: str, test_sections: list[Section]
):
    """Тест поиска секций по названию."""
    response = await test_client.get(
        "/api/v1/sections?search=Section 1", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert "Section 1" in data["items"][0]["name"]


@pytest.mark.asyncio
async def test_get_sections_sorting(test_client: AsyncClient, user_token: str):
    """Тест сортировки секций."""

    response = await test_client.get(
        "/api/v1/sections?sort_by=id&order=desc", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    ids = [item["id"] for item in data["items"]]
    assert ids == sorted(ids, reverse=True)


@pytest.mark.asyncio
async def test_get_sections_available_only(
    test_client: AsyncClient, user_token: str
):
    """Тест фильтрации по доступности мест."""
    response = await test_client.get(
        "/api/v1/sections?available_only=true", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    for item in data["items"]:
        assert item["available_spots"] > 0


@pytest.mark.asyncio
async def test_get_sections_unauthorized(test_client: AsyncClient):
    """Тест получения секций без авторизации."""
    response = await test_client.get("/api/v1/sections")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_section_by_id_success(
    test_client: AsyncClient, user_token: str, test_section: Section
):
    """Тест успешного получения секции по ID."""
    response = await test_client.get(
        f"/api/v1/sections/{test_section.id}", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_section.id
    assert data["name"] == test_section.name
    assert data["description"] == test_section.description
    assert "students" in data


@pytest.mark.asyncio
async def test_get_section_with_students(
    test_client: AsyncClient, user_token: str, section_with_students: Section,
):
    """Тест получения секции со списком студентов."""
    response = await test_client.get(
        f"/api/v1/sections/{section_with_students.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert "students" in data
    assert len(data["students"]) == 3

    student_info = data["students"][0]
    assert "student_id" in student_info
    assert "first_name" in student_info
    assert "last_name" in student_info
    assert "email" in student_info
    assert "enrollment_date" in student_info


@pytest.mark.asyncio
async def test_get_section_not_found(test_client: AsyncClient, user_token: str):
    """Тест получения несуществующей секции."""
    response = await test_client.get(
        "/api/v1/sections/99999", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_section_unauthorized(test_client: AsyncClient, test_section: Section):
    """Тест получения секции без авторизации."""
    response = await test_client.get(f"/api/v1/sections/{test_section.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_section_success(
    test_client: AsyncClient, admin_token: str, test_db: AsyncSession,
):
    """Тест успешного создания секции."""
    section_data = SectionFactory.build()

    response = await test_client.post(
        "/api/v1/sections",
        json=section_data.model_dump(),
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == section_data.name
    assert data["description"] == section_data.description
    assert data["max_capacity"] == section_data.max_capacity
    assert "id" in data

    result = await test_db.execute(
        select(Section).where(Section.id == data["id"])
    )
    db_section = result.scalar_one_or_none()
    assert db_section is not None
    assert db_section.name == section_data.name


@pytest.mark.asyncio
async def test_create_section_duplicate_name(
    test_client: AsyncClient, admin_token: str, test_section: Section,
):
    """Тест создания секции с существующим названием."""
    section_data = SectionFactory.build(name=test_section.name)

    response = await test_client.post(
        "/api/v1/sections",
        json=section_data.model_dump(),
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_section_validation_error(
    test_client: AsyncClient, admin_token: str,
):
    """Тест валидации при создании секции."""
    invalid_data = {"name": "", "max_capacity": 0}

    response = await test_client.post(
        "/api/v1/sections",
        json=invalid_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_section_forbidden_for_user(test_client: AsyncClient, user_token: str):
    """Тест запрета создания секции для обычного пользователя."""
    section_data = SectionFactory.build()

    response = await test_client.post(
        "/api/v1/sections",
        json=section_data.model_dump(),
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_section_unauthorized(test_client: AsyncClient):
    """Тест создания секции без авторизации."""
    section_data = SectionFactory.build()

    response = await test_client.post("/api/v1/sections", json=section_data.model_dump())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_section_success(
    test_client: AsyncClient,
    admin_token: str,
    test_section: Section,
    test_db: AsyncSession,
):
    """Тест успешного обновления секции."""
    update_data = SectionUpdateFactory.build()

    response = await test_client.put(
        f"/api/v1/sections/{test_section.id}",
        json=update_data.model_dump(exclude_none=True),
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_section.id
    assert data["name"] == update_data.name

    await test_db.refresh(test_section)
    assert test_section.name == update_data.name


@pytest.mark.asyncio
async def test_update_section_partial(
    test_client: AsyncClient, admin_token: str, test_section: Section
):
    """Тест частичного обновления секции."""
    original_name = test_section.name
    update_data = {"description": "New description only"}

    response = await test_client.put(
        f"/api/v1/sections/{test_section.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == original_name
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_update_section_duplicate_name(
    test_client: AsyncClient, admin_token: str, test_sections: list[Section]
):
    """Тест обновления секции с названием другой секции."""
    section_to_update = test_sections[0]
    existing_name = test_sections[1].name

    update_data = {"name": existing_name}

    response = await test_client.put(
        f"/api/v1/sections/{section_to_update.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_section_capacity_below_enrollment(
    test_client: AsyncClient, admin_token: str, section_with_students: Section,
):
    """Тест обновления вместимости ниже текущего количества студентов."""

    update_data = {"max_capacity": 2}

    response = await test_client.put(
        f"/api/v1/sections/{section_with_students.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 422
    assert "enrollment" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_section_not_found(test_client: AsyncClient, admin_token: str):
    """Тест обновления несуществующей секции."""
    update_data = SectionUpdateFactory.build()

    response = await test_client.put(
        "/api/v1/sections/99999",
        json=update_data.model_dump(exclude_none=True),
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_section_forbidden_for_user(
    test_client: AsyncClient, user_token: str, test_section: Section
):
    """Тест запрета обновления секции для обычного пользователя."""
    update_data = {"name": "New Name"}

    response = await test_client.put(
        f"/api/v1/sections/{test_section.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_section_success(
    test_client: AsyncClient,
    admin_token: str,
    test_section: Section,
    test_db: AsyncSession,
):
    """Тест успешного удаления секции."""
    section_id = test_section.id

    response = await test_client.delete(
        f"/api/v1/sections/{section_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204

    result = await test_db.execute(
        select(Section).where(Section.id == section_id)
    )
    db_section = result.scalar_one_or_none()
    assert db_section is None


@pytest.mark.asyncio
async def test_delete_section_with_students(
    test_client: AsyncClient, admin_token: str, section_with_students: Section
):
    """Тест удаления секции со студентами (должно быть запрещено)."""
    response = await test_client.delete(
        f"/api/v1/sections/{section_with_students.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 422
    assert "enrolled students" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_section_not_found(test_client: AsyncClient, admin_token: str):
    """Тест удаления несуществующей секции."""
    response = await test_client.delete(
        "/api/v1/sections/99999", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_section_forbidden_for_user(
    test_client: AsyncClient, user_token: str, test_section: Section
):
    """Тест запрета удаления секции для обычного пользователя."""
    response = await test_client.delete(
        f"/api/v1/sections/{test_section.id}", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_section_unauthorized(test_client: AsyncClient, test_section: Section):
    """Тест удаления секции без авторизации."""
    response = await test_client.delete(f"/api/v1/sections/{test_section.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_section_capacity_tracking(
    test_client: AsyncClient,
    user_token: str,
    test_section: Section,
    test_db: AsyncSession,
):
    """Тест корректного отслеживания заполненности секции."""

    for i in range(5):
        student = Student(
            first_name=f"Student{i}",
            last_name=f"Last{i}",
            email=f"capacity_test_{i}@test.com",
            date_of_birth=datetime.date(2000, 1, 1),
        )
        test_db.add(student)
        await test_db.commit()
        await test_db.refresh(student)

        enrollment = StudentSection(
            student_id=student.id,
            section_id=test_section.id,
            enrollment_date=datetime.date.today(),
        )
        test_db.add(enrollment)

    await test_db.commit()

    response = await test_client.get(
        f"/api/v1/sections/{test_section.id}", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["current_enrollment"] == 5
    assert data["available_spots"] == test_section.max_capacity - 5
    assert data["is_full"] == (5 >= test_section.max_capacity)


@pytest.mark.asyncio
async def test_create_multiple_sections_batch(
    test_client: AsyncClient, admin_token: str, test_db: AsyncSession
):
    """Тест создания нескольких секций подряд."""
    sections_data = [SectionFactory.build() for _ in range(3)]

    created_ids = []
    for section_data in sections_data:
        response = await test_client.post(
            "/api/v1/sections",
            json=section_data.model_dump(),
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    result = await test_db.execute(
        select(Section).where(Section.id.in_(created_ids))
    )
    db_sections = result.scalars().all()
    assert len(db_sections) == 3


@pytest.mark.asyncio
async def test_search_with_special_characters(
    test_client: AsyncClient, user_token: str, admin_token: str
):
    """Тест поиска с специальными символами."""

    section_data = {
        "name": "C++ Programming Course",
        "description": "Learn C++ & OOP fundamentals",
        "max_capacity": 20
    }

    create_response = await test_client.post(
        "/api/v1/sections",
        json=section_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert create_response.status_code == 201

    response = await test_client.get(
        "/api/v1/sections",
        params={"search": "C++"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_section_is_full_logic(
    test_client: AsyncClient, user_token: str, admin_token: str
):
    """Тест логики определения заполненности секции."""

    section_data = {
        "name": "Small Section",
        "description": "Section with capacity 3",
        "max_capacity": 3,
    }

    create_response = await test_client.post(
        "/api/v1/sections",
        json=section_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert create_response.status_code == 201
    section = create_response.json()
    section_id = section["id"]

    response = await test_client.get(
        f"/api/v1/sections/{section_id}", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["is_full"] is False

    for i in range(3):
        student_data = {
            "first_name": f"Student{i}",
            "last_name": f"Last{i}",
            "email": f"full_test_{i}@test.com",
            "date_of_birth": "2000-01-01",
        }

        student_response = await test_client.post(
            "/api/v1/students",
            json=student_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert student_response.status_code == 201
        student_id = student_response.json()["id"]

        enroll_response = await test_client.post(
            f"/api/v1/students/{student_id}/sections/{section_id}",
            json={"enrollment_date": "2025-01-20"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert enroll_response.status_code == 201

    response = await test_client.get(
        f"/api/v1/sections/{section_id}", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_enrollment"] == 3
    assert data["is_full"] is True
    assert data["available_spots"] == 0


@pytest.mark.asyncio
async def test_available_sections_filter_logic(
    test_client: AsyncClient, user_token: str, test_db: AsyncSession,
):
    """Тест фильтра доступных секций."""

    full_section = Section(
        name="Full Section",
        description="Completely full",
        max_capacity=3,
    )
    test_db.add(full_section)
    await test_db.commit()
    await test_db.refresh(full_section)

    for i in range(3):
        student = Student(
            first_name=f"FullStudent{i}",
            last_name=f"Last{i}",
            email=f"full_student_{i}@test.com",
            date_of_birth=datetime.date(2000, 1, 1),
        )
        test_db.add(student)
        await test_db.commit()
        await test_db.refresh(student)

        enrollment = StudentSection(
            student_id=student.id,
            section_id=full_section.id,
            enrollment_date=datetime.date.today(),
        )
        test_db.add(enrollment)

    await test_db.commit()

    available_section = Section(
        name="Available Section",
        description="Has space",
        max_capacity=5,
    )
    test_db.add(available_section)
    await test_db.commit()

    response = await test_client.get(
        "/api/v1/sections?available_only=true", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    section_names = [item["name"] for item in data["items"]]
    assert "Available Section" in section_names
    assert "Full Section" not in section_names


@pytest.mark.asyncio
async def test_section_cascade_delete_students(
    test_client: AsyncClient,
    admin_token: str,
    test_db: AsyncSession,
):
    """Тест каскадного удаления связей при удалении секции после отчисления студентов."""
    section = Section(
        name="Cascade Test Section",
        description="For cascade delete test",
        max_capacity=20,
    )
    test_db.add(section)
    await test_db.commit()
    await test_db.refresh(section)

    student = Student(
        first_name="Cascade",
        last_name="Test",
        email="cascade@test.com",
        date_of_birth=datetime.date(2000, 1, 1),
    )
    test_db.add(student)
    await test_db.commit()
    await test_db.refresh(student)

    enrollment = StudentSection(
        student_id=student.id,
        section_id=section.id,
        enrollment_date=datetime.date.today(),
    )
    test_db.add(enrollment)
    await test_db.commit()

    response = await test_client.delete(
        f"/api/v1/sections/{section.id}", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 422

    await test_db.delete(enrollment)
    await test_db.commit()

    response = await test_client.delete(
        f"/api/v1/sections/{section.id}", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204

    result = await test_db.execute(
        select(Student).where(Student.id == student.id)
    )
    db_student = result.scalar_one_or_none()
    assert db_student is not None
