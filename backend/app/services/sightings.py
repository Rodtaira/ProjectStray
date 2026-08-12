from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sighting import Sighting
from app.schemas.sighting import SightingCreate, SightingRead


async def create_sighting(db: AsyncSession, data: SightingCreate, reporter_id) -> Sighting:
    point = from_shape(Point(data.longitude, data.latitude), srid=4326)
    sighting = Sighting(description=data.description, location=point, reporter_id=reporter_id)
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)
    return sighting


async def list_sightings(db: AsyncSession, limit: int = 50) -> list[Sighting]:
    result = await db.execute(
        select(Sighting).order_by(Sighting.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


def to_read_schema(sighting: Sighting) -> SightingRead:
    """Converte o modelo ORM (coluna Geography) pro schema de resposta
    (lat/lon simples) — é aqui que fica a tradução entre PostGIS e JSON.
    """
    point = to_shape(sighting.location)
    return SightingRead(
        id=sighting.id,
        reporter_id=sighting.reporter_id,
        description=sighting.description,
        latitude=point.y,
        longitude=point.x,
        created_at=sighting.created_at,
    )
