from datetime import date, timedelta
from random import randint, sample

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Section, Student, StudentSection

SECTIONS_DATA = [
    {
        "name": "Python Programming",
        "description": (
            "Learn Python from basics to advanced topics including OOP, async programming, "
            "and web development"
        ),
        "max_capacity": 25,
    },
    {
        "name": "Mathematics for CS",
        "description": (
            "Discrete mathematics, linear algebra, and calculus for computer science students"
        ),
        "max_capacity": 30,
    },
    {
        "name": "Physics Laboratory",
        "description": "Hands-on experiments in mechanics, thermodynamics, and electromagnetism",
        "max_capacity": 20,
    },
    {
        "name": "Data Structures & Algorithms",
        "description": (
            "Study of fundamental data structures and algorithmic problem-solving techniques"
        ),
        "max_capacity": 22,
    },
    {
        "name": "Web Development",
        "description": "Full-stack web development with modern frameworks and best practices",
        "max_capacity": 28,
    },
    {
        "name": "Machine Learning Basics",
        "description": (
            "Introduction to ML concepts, supervised and unsupervised learning algorithms"
        ),
        "max_capacity": 20,
    },
    {
        "name": "Database Systems",
        "description": "Relational databases, SQL, NoSQL, and database design principles",
        "max_capacity": 25,
    },
]


STUDENTS_DATA = [
    {
        "first_name": "Alice",
        "last_name": "Johnson",
        "email": "alice.johnson@example.com",
        "year_offset": 20,
    },
    {
        "first_name": "Bob",
        "last_name": "Smith",
        "email": "bob.smith@example.com",
        "year_offset": 19,
    },
    {
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie.brown@example.com",
        "year_offset": 21,
    },
    {
        "first_name": "Diana",
        "last_name": "Williams",
        "email": "diana.williams@example.com",
        "year_offset": 18,
    },
    {
        "first_name": "Edward",
        "last_name": "Davis",
        "email": "edward.davis@example.com",
        "year_offset": 22,
    },
    {
        "first_name": "Fiona",
        "last_name": "Miller",
        "email": "fiona.miller@example.com",
        "year_offset": 20,
    },
    {
        "first_name": "George",
        "last_name": "Wilson",
        "email": "george.wilson@example.com",
        "year_offset": 19,
    },
    {
        "first_name": "Hannah",
        "last_name": "Moore",
        "email": "hannah.moore@example.com",
        "year_offset": 21,
    },
    {
        "first_name": "Ivan",
        "last_name": "Taylor",
        "email": "ivan.taylor@example.com",
        "year_offset": 20,
    },
    {
        "first_name": "Julia",
        "last_name": "Anderson",
        "email": "julia.anderson@example.com",
        "year_offset": 18,
    },
    {
        "first_name": "Kevin",
        "last_name": "Thomas",
        "email": "kevin.thomas@example.com",
        "year_offset": 22,
    },
    {
        "first_name": "Laura",
        "last_name": "Jackson",
        "email": "laura.jackson@example.com",
        "year_offset": 19,
    },
    {
        "first_name": "Michael",
        "last_name": "White",
        "email": "michael.white@example.com",
        "year_offset": 21,
    },
    {
        "first_name": "Nina",
        "last_name": "Harris",
        "email": "nina.harris@example.com",
        "year_offset": 20,
    },
    {
        "first_name": "Oliver",
        "last_name": "Martin",
        "email": "oliver.martin@example.com",
        "year_offset": 19,
    },
]


async def check_demo_data_exists(db: AsyncSession) -> bool:
    """
    Проверить существуют ли уже демо-данные.

    Args:
        db: Асинхронная сессия БД

    Returns:
        True если данные уже загружены
    """
    result = await db.execute(select(func.count()).select_from(Student))
    student_count = result.scalar_one()

    return student_count > 0


async def seed_sections(db: AsyncSession) -> list[Section]:
    """
    Создать демо-секции.

    Args:
        db: Асинхронная сессия БД

    Returns:
        Список созданных секций
    """
    sections = []

    for section_data in SECTIONS_DATA:
        result = await db.execute(select(Section).where(Section.name == section_data["name"]))
        existing_section = result.scalar_one_or_none()

        if existing_section:
            sections.append(existing_section)
            continue

        section = Section(**section_data)
        db.add(section)
        sections.append(section)

    await db.commit()

    for section in sections:
        await db.refresh(section)

    print(f"Created {len(sections)} sections")
    return sections


async def seed_students(db: AsyncSession) -> list[Student]:
    """
    Создать демо-студентов.

    Args:
        db: Асинхронная сессия БД

    Returns:
        Список созданных студентов
    """
    students = []
    today = date.today()

    for student_data in STUDENTS_DATA:
        result = await db.execute(select(Student).where(Student.email == student_data["email"]))
        existing_student = result.scalar_one_or_none()

        if existing_student:
            students.append(existing_student)
            continue

        year_offset = student_data.pop("year_offset")
        birth_year = today.year - year_offset
        date_of_birth = date(birth_year, randint(1, 12), randint(1, 28))

        student = Student(**student_data, date_of_birth=date_of_birth)
        db.add(student)
        students.append(student)

    await db.commit()

    for student in students:
        await db.refresh(student)

    print(f"Created {len(students)} students")
    return students


async def seed_enrollments(
    db: AsyncSession, students: list[Student], sections: list[Section]
) -> int:
    """
    Создать записи студентов в секции.

    Каждый студент записывается в 1-3 секции со случайными датами зачисления.

    Args:
        db: Асинхронная сессия БД
        students: Список студентов
        sections: Список секций

    Returns:
        Количество созданных записей
    """
    enrollments_count = 0
    today = date.today()

    for student in students:
        num_sections = randint(1, min(3, len(sections)))

        student_sections = sample(sections, num_sections)

        for section in student_sections:
            result = await db.execute(
                select(StudentSection).where(
                    StudentSection.student_id == student.id, StudentSection.section_id == section.id
                )
            )
            existing_enrollment = result.scalar_one_or_none()

            if existing_enrollment:
                continue

            result = await db.execute(
                select(func.count())
                .select_from(StudentSection)
                .where(StudentSection.section_id == section.id)
            )
            current_enrollment = result.scalar_one()

            if current_enrollment >= section.max_capacity:
                continue

            days_ago = randint(1, 180)
            enrollment_date = today - timedelta(days=days_ago)

            enrollment = StudentSection(
                student_id=student.id, section_id=section.id, enrollment_date=enrollment_date
            )
            db.add(enrollment)
            enrollments_count += 1

    await db.commit()

    print(f"Created {enrollments_count} student enrollments")
    return enrollments_count


async def seed_demo_data(db: AsyncSession) -> None:
    """
    Загрузить все демонстрационные данные в БД.

    Создает:
    - 7 секций
    - 15 студентов
    - 15-25 записей студентов в секции (случайное количество)

    Args:
        db: Асинхронная сессия БД
    """
    print("\n" + "=" * 60)
    print("Loading demo data...")
    print("=" * 60 + "\n")

    try:
        if await check_demo_data_exists(db):
            print("Demo data already exists. Skipping...")
            print("\n" + "=" * 60 + "\n")
            return None

        print("Creating sections...")
        sections = await seed_sections(db)

        print("\nCreating students...")
        students = await seed_students(db)

        print("\nCreating student enrollments...")
        enrollments_count = await seed_enrollments(db, students, sections)

        print("\n" + "=" * 60)
        print("Demo data loaded successfully!")
        print(f"   - Sections: {len(sections)}")
        print(f"   - Students: {len(students)}")
        print(f"   - Enrollments: {enrollments_count}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError loading demo data: {e}")
        await db.rollback()
        raise
