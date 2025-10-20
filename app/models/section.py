from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Section(Base, TimestampMixin):
    """Модель секции."""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    students: Mapped[list["StudentSection"]] = relationship(  # noqa: F821
        "StudentSection", back_populates="section", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Section(id={self.id}, name={self.name!r}, capacity={self.max_capacity})"
