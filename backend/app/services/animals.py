from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.animal import Animal, AnimalSex, AnimalSpecies, AnimalStatus
from app.schemas.animal import AnimalCreate, AnimalRead, AnimalUpdate


async def create_animal(db: AsyncSession, data: AnimalCreate, registered_by) -> Animal:
    animal = Animal(
        species=AnimalSpecies(data.species),
        sex=AnimalSex(data.sex),
        name=data.name,
        description=data.description,
        registered_by=registered_by,
    )
    db.add(animal)
    await db.commit()
    await db.refresh(animal)
    return animal


async def get_animal_by_id(db: AsyncSession, animal_id) -> Animal | None:
    result = await db.execute(select(Animal).where(Animal.id == animal_id))
    return result.scalar_one_or_none()


async def list_animals(
    db: AsyncSession,
    species: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Animal]:
    query = select(Animal).order_by(Animal.created_at.desc()).limit(limit)
    if species is not None:
        query = query.where(Animal.species == AnimalSpecies(species))
    if status is not None:
        query = query.where(Animal.status == AnimalStatus(status))
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_animal(db: AsyncSession, animal: Animal, data: AnimalUpdate) -> Animal:
    if data.name is not None:
        animal.name = data.name
    if data.description is not None:
        animal.description = data.description
    if data.sex is not None:
        animal.sex = AnimalSex(data.sex)
    if data.is_sterilized is not None:
        animal.is_sterilized = data.is_sterilized
    if data.status is not None:
        animal.status = AnimalStatus(data.status)
    await db.commit()
    await db.refresh(animal)
    return animal


async def delete_animal(db: AsyncSession, animal: Animal) -> None:
    """Exclusão de verdade — só pra corrigir cadastro feito por engano.
    Mudança de ciclo de vida (adotado, falecido) deve usar status, não isso."""
    await db.delete(animal)
    await db.commit()


def to_read_schema(animal: Animal) -> AnimalRead:
    return AnimalRead(
        id=animal.id,
        registered_by=animal.registered_by,
        species=animal.species.value,
        sex=animal.sex.value,
        name=animal.name,
        description=animal.description,
        is_sterilized=animal.is_sterilized,
        status=animal.status.value,
        photo_url=f"/api/v1/animals/{animal.id}/photo" if animal.photo_key else None,
        created_at=animal.created_at,
    )

import uuid

from starlette.concurrency import run_in_threadpool

from app.services import storage


async def set_animal_photo(db: AsyncSession, animal: Animal, processed_bytes: bytes) -> Animal:
    """Envia a foto já processada (sem EXIF, já em JPEG) pro storage, grava
    a chave nova no animal, e remove a chave antiga se estava substituindo
    uma foto existente."""
    new_key = f"animals/{animal.id}/{uuid.uuid4().hex}.jpg"
    old_key = animal.photo_key

    await run_in_threadpool(storage.upload_bytes, new_key, processed_bytes, "image/jpeg")

    animal.photo_key = new_key
    await db.commit()
    await db.refresh(animal)

    if old_key:
        await run_in_threadpool(storage.delete_object, old_key)

    return animal
