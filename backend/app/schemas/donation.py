import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class DonationCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)


class DonationRead(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    donor_id: uuid.UUID | None
    amount: Decimal
    status: str
    created_at: datetime


class DonationCheckout(BaseModel):
    donation: DonationRead
    checkout_url: str
