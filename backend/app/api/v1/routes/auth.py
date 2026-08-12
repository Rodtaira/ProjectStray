from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.auth import RefreshRequest, Token
from app.schemas.user import UserLogin, UserRegister
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)) -> Token:
    existing = await auth_service.get_user_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com esse e-mail")

    user = await auth_service.register_user(
        db, email=data.email, password=data.password, full_name=data.full_name, phone=data.phone
    )
    return Token(
        access_token=auth_service.create_access_token(str(user.id)),
        refresh_token=auth_service.create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    user = await auth_service.get_user_by_email(db, data.email)

    # Checagem única pra e-mail inexistente E senha errada — a mensagem de
    # erro é a mesma nos dois casos de propósito, pra não revelar pra quem
    # está tentando adivinhar se um e-mail está cadastrado ou não.
    if (
        user is None
        or user.deleted_at is not None
        or not auth_service.verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos")

    return Token(
        access_token=auth_service.create_access_token(str(user.id)),
        refresh_token=auth_service.create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=Token)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)) -> Token:
    try:
        user_id = auth_service.decode_token(data.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido ou expirado")

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado")

    return Token(
        access_token=auth_service.create_access_token(str(user.id)),
        refresh_token=auth_service.create_refresh_token(str(user.id)),
    )