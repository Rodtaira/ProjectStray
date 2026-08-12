import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.animal import AnimalCreate, AnimalRead, AnimalUpdate
from app.services import animals as animals_service

router = APIRouter(prefix="/animals", tags=["animals"])


@router.post("", response_model=AnimalRead, status_code=status.HTTP_201_CREATED)
async def create_animal(
    data: AnimalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnimalRead:
    animal = await animals_service.create_animal(db, data, registered_by=current_user.id)
    return animals_service.to_read_schema(animal)


@router.get("", response_model=list[AnimalRead], dependencies=[Depends(get_current_user)])
async def list_animals(
    db: AsyncSession = Depends(get_db),
    species: Literal["dog", "cat"] | None = Query(default=None),
    status_filter: Literal["stray", "adopted", "in_shelter", "deceased"] | None = Query(
        default=None, alias="status"
    ),
) -> list[AnimalRead]:
    animals = await animals_service.list_animals(db, species=species, status=status_filter)
    return [animals_service.to_read_schema(a) for a in animals]


@router.get("/{animal_id}", response_model=AnimalRead, dependencies=[Depends(get_current_user)])
async def get_animal(
    animal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnimalRead:
    animal = await animals_service.get_animal_by_id(db, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal não encontrado")
    return animals_service.to_read_schema(animal)


@router.patch("/{animal_id}", response_model=AnimalRead)
async def update_animal(
    animal_id: uuid.UUID,
    data: AnimalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnimalRead:
    animal = await animals_service.get_animal_by_id(db, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal não encontrado")

    is_owner = animal.registered_by == current_user.id
    is_moderator = current_user.role in (UserRole.moderator, UserRole.admin)
    if not is_owner and not is_moderator:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Só quem registrou o animal ou um moderador pode editar"
        )

    updated = await animals_service.update_animal(db, animal, data)
    return animals_service.to_read_schema(updated)


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    animal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    animal = await animals_service.get_animal_by_id(db, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal não encontrado")

    is_owner = animal.registered_by == current_user.id
    is_moderator = current_user.role in (UserRole.moderator, UserRole.admin)
    if not is_owner and not is_moderator:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Só quem registrou o animal ou um moderador pode remover"
        )

    await animals_service.delete_animal(db, animal)