import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def common_validate_date_of_birth(date_value: datetime.date | None) -> datetime.date | None:
    """Валидация даты рождения при обновлении."""
    if date_value is None:
        return date_value

    today = datetime.date.today()
    age = (
        today.year
        - date_value.year
        - ((today.month, today.day) < (date_value.month, date_value.day))
    )

    if age < 15:
        raise ValueError("Student must be at least 15 years old")
    if age > 100:
        raise ValueError("Invalid date of birth")

    return date_value


class StudentBase(BaseModel):
    """Базовая схема студента."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    date_of_birth: datetime.date

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: datetime.date) -> datetime.date:
        """Валидация даты рождения - студент должен быть не младше 15 лет."""

        return common_validate_date_of_birth(date_value=v)


class StudentCreate(StudentBase):
    """Схема для создания студента."""

    ...


class StudentUpdate(BaseModel):
    """Схема для обновления студента."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    date_of_birth: datetime.date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: datetime.date | None) -> datetime.date | None:
        """Валидация даты рождения при обновлении."""

        return common_validate_date_of_birth(date_value=v)


class StudentSectionInfo(BaseModel):
    """Информация о секции для студента."""

    model_config = ConfigDict(from_attributes=True)

    section_id: int
    section_name: str
    enrollment_date: datetime.date


class StudentResponse(StudentBase):
    """Схема ответа с данными студента."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    full_name: str


class StudentDetailResponse(StudentResponse):
    """Детальная схема студента со списком секций."""

    sections: list[StudentSectionInfo] = []


class EnrollmentRequest(BaseModel):
    """Схема для записи студента в секцию."""

    enrollment_date: datetime.date = Field(default_factory=datetime.date.today)

    @field_validator("enrollment_date")
    @classmethod
    def validate_enrollment_date(cls, v: datetime.date) -> datetime.date:
        """Валидация даты зачисления - не должна быть в будущем."""
        if v > datetime.date.today():
            raise ValueError("Enrollment date cannot be in the future")
        return v
