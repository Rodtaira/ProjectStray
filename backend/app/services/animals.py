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
        created_at=animal.created_at,
    )