import decimal
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DonationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    refunded = "refunded"


class Donation(Base):
    """Registro de doação — o ledger de transparência do crowdfunding.
    payment_reference guarda o id da preferência criada no Mercado Pago
    (útil pra auditoria), mas a confirmação via webhook casa pelo id da
    própria doação (external_reference), não por esse campo.
    """

    __tablename__ = "donations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True
    )
    donor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    amount: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_reference: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status"),
        nullable=False,
        default=DonationStatus.pending,
        server_default=DonationStatus.pending.value,
    )

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())