import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnimalSpecies(str, enum.Enum):
    dog = "dog"
    cat = "cat"


class AnimalSex(str, enum.Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


class AnimalStatus(str, enum.Enum):
    stray = "stray"
    adopted = "adopted"
    in_shelter = "in_shelter"
    deceased = "deceased"


class Animal(Base):
    """Registro individual de um animal (comunitário, de rua, etc.) —
    diferente de Sighting, que é um relato pontual de avistamento.
    """

    __tablename__ = "animals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    registered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    species: Mapped[AnimalSpecies] = mapped_column(
        Enum(AnimalSpecies, name="animal_species"), nullable=False
    )
    sex: Mapped[AnimalSex] = mapped_column(
        Enum(AnimalSex, name="animal_sex"),
        nullable=False,
        default=AnimalSex.unknown,
        server_default=AnimalSex.unknown.value,
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_sterilized: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    status: Mapped[AnimalStatus] = mapped_column(
        Enum(AnimalStatus, name="animal_status"),
        nullable=False,
        default=AnimalStatus.stray,
        server_default=AnimalStatus.stray.value,
    )

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())