from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserMe, UserPublic
from app.services import auth as auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
async def get_me(user: User = Depends(get_current_user)) -> UserMe:
    return UserMe.model_validate(user)


@router.patch("/me", dependencies=[Depends(get_current_user)])
async def update_me():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.delete("/me", dependencies=[Depends(get_current_user)])
async def delete_me():
    """Aciona a rotina de anonimização já combinada — aqui só fica o gancho
    (marcar deleted_at e disparar o processo). Nunca deleta em cascata
    sightings/doações/mensagens, só sobrescreve PII."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_public(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> UserPublic:
    target = await auth_service.get_user_by_id(db, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    return UserPublic.model_validate(target)
