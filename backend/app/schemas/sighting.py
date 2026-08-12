import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SightingCreate(BaseModel):
    description: str | None = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class SightingUpdate(BaseModel):
    description: str | None = None
    status: Literal["open", "resolved"] | None = None


class SightingRead(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    description: str | None
    status: str
    latitude: float
    longitude: float
    created_at: datetime
