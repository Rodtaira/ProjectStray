import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.sighting import SightingCreate, SightingRead, SightingUpdate
from app.services import sightings as sightings_service

router = APIRouter(prefix="/sightings", tags=["sightings"])


@router.post(
    "",
    response_model=SightingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sighting(
    data: SightingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SightingRead:
    sighting = await sightings_service.create_sighting(db, data, reporter_id=current_user.id)
    return sightings_service.to_read_schema(sighting)


@router.get("", response_model=list[SightingRead], dependencies=[Depends(get_current_user)])
async def list_sightings(
    db: AsyncSession = Depends(get_db),
) -> list[SightingRead]:
    sightings = await sightings_service.list_sightings(db)
    return [sightings_service.to_read_schema(s) for s in sightings]


@router.get("/{sighting_id}", response_model=SightingRead, dependencies=[Depends(get_current_user)])
async def get_sighting(
    sighting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SightingRead:
    sighting = await sightings_service.get_sighting_by_id(db, sighting_id)
    if sighting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Relato não encontrado")
    return sightings_service.to_read_schema(sighting)


@router.patch("/{sighting_id}", response_model=SightingRead)
async def update_sighting(
    sighting_id: uuid.UUID,
    data: SightingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SightingRead:
    sighting = await sightings_service.get_sighting_by_id(db, sighting_id)
    if sighting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Relato não encontrado")

    is_owner = sighting.reporter_id == current_user.id
    is_moderator = current_user.role in (UserRole.moderator, UserRole.admin)
    if not is_owner and not is_moderator:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Só o autor do relato ou um moderador pode editar"
        )

    updated = await sightings_service.update_sighting(db, sighting, data)
    return sightings_service.to_read_schema(updated)


@router.get("/{sighting_id}/matches")
async def get_sighting_matches(sighting_id: uuid.UUID):
    """Candidatos sugeridos via pgvector — depende do worker de embedding,
    que ainda não existe. Fica pra quando montarmos app/workers/.
    """
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")
