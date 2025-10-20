from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class Role(Base, TimestampMixin):
    """Модель роли."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Role(id={self.id}, name={self.name!r})"

    @property
    def is_admin(self) -> bool:
        """Проверка является ли роль админской."""
        return self.name.lower() == "admin"
