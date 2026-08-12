import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AnimalCreate(BaseModel):
    species: Literal["dog", "cat"]
    sex: Literal["male", "female", "unknown"] = "unknown"
    name: str | None = None
    description: str | None = None


class AnimalUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sex: Literal["male", "female", "unknown"] | None = None
    is_sterilized: bool | None = None
    status: Literal["stray", "adopted", "in_shelter", "deceased"] | None = None


class AnimalRead(BaseModel):
    id: uuid.UUID
    registered_by: uuid.UUID
    species: str
    sex: str
    name: str | None
    description: str | None
    is_sterilized: bool
    status: str
    created_at: datetime
