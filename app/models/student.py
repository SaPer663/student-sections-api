from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Student(Base, TimestampMixin):
    """Модель студента."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    sections: Mapped[list["StudentSection"]] = relationship(  # noqa: F821
        "StudentSection", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Student(id={self.id}, name={self.first_name} {self.last_name}, email={self.email!r})"
        )

    @property
    def full_name(self) -> str:
        """Полное имя студента."""
        return f"{self.first_name} {self.last_name}"
