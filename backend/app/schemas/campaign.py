import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    title: str
    description: str | None = None
    goal_amount: Decimal = Field(..., gt=0)
    animal_id: uuid.UUID | None = None


class CampaignUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Literal["active", "funded", "completed", "cancelled"] | None = None


class CampaignRead(BaseModel):
    id: uuid.UUID
    created_by: uuid.UUID
    animal_id: uuid.UUID | None
    title: str
    description: str | None
    goal_amount: Decimal
    status: str
    created_at: datetime