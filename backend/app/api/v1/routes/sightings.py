from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.sighting import SightingCreate, SightingRead
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


@router.get("/{sighting_id}/matches")
async def get_sighting_matches(sighting_id: str):
    """Candidatos sugeridos via pgvector — depende do worker de embedding,
    que ainda não existe. Fica pra quando montarmos app/workers/.
    """
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")
