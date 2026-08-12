import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # 72 = limite do bcrypt
    full_name: str | None = None
    phone: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserMe(BaseModel):
    """Perfil completo — só o próprio usuário vê isso, via /users/me."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    phone: str | None
    full_name: str | None
    role: str
    created_at: datetime


class UserPublic(BaseModel):
    """Perfil público de OUTRO usuário — nunca inclui email ou telefone."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None
    role: str