import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SightingCreate(BaseModel):
    description: str | None = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class SightingRead(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    description: str | None
    latitude: float
    longitude: float
    created_at: datetime
