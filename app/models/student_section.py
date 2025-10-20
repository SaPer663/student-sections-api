from datetime import date

from sqlalchemy import Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class StudentSection(Base, TimestampMixin):
    """
    Модель связи студента и секции.

    Реализует Many-to-Many связь с дополнительными данными (дата зачисления).
    """

    __tablename__ = "student_sections"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
    )
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE"),
        primary_key=True,
    )

    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="sections")  # noqa: F821
    section: Mapped["Section"] = relationship("Section", back_populates="students")  # noqa: F821

    __table_args__ = (UniqueConstraint("student_id", "section_id", name="uq_student_section"),)

    def __repr__(self) -> str:
        return (
            f"StudentSection(student_id={self.student_id}, "
            f"section_id={self.section_id}, enrollment_date={self.enrollment_date})"
        )
