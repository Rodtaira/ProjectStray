import enum
import uuid

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserRole(str, enum.Enum):
    common = "common"
    moderator = "moderator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.common, nullable=False
    )

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Preenchido pela rotina de exclusão/anonimização — nunca deletamos a linha,
    # só sobrescrevemos PII e marcamos quando isso aconteceu.
    deleted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
