import decimal
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CampaignStatus(str, enum.Enum):
    active = "active"
    funded = "funded"
    completed = "completed"
    cancelled = "cancelled"


class Campaign(Base):
    """Campanha de crowdfunding — geralmente pra castração, priorizando
    fêmeas conforme a missão do app. Pode estar vinculada a um animal
    específico ou ser regional/geral (animal_id nulo).
    """

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("animals.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    goal_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        nullable=False,
        default=CampaignStatus.active,
        server_default=CampaignStatus.active.value,
    )

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
