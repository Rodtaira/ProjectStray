from geoalchemy2.shape import from_shape, to_shape # type: ignore
from shapely.geometry import Point # type: ignore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sighting import Sighting, SightingStatus
from app.schemas.sighting import SightingCreate, SightingRead, SightingUpdate

# 3 casas decimais ≈ 100-110m de margem — suficiente pra proteger onde
# exatamente a pessoa estava ao reportar (potencialmente perto de casa),
# sem inutilizar o mapa pra quem quer saber "tem animal perto daqui".
# A coordenada EXATA continua no banco, intacta — isso só afeta a resposta.
PUBLIC_COORDINATE_PRECISION = 3


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


async def get_sighting_by_id(db: AsyncSession, sighting_id) -> Sighting | None:
    result = await db.execute(select(Sighting).where(Sighting.id == sighting_id))
    return result.scalar_one_or_none()


async def update_sighting(db: AsyncSession, sighting: Sighting, data: SightingUpdate) -> Sighting:
    if data.description is not None:
        sighting.description = data.description
    if data.status is not None:
        sighting.status = SightingStatus(data.status)
    await db.commit()
    await db.refresh(sighting)
    return sighting


def to_read_schema(sighting: Sighting) -> SightingRead:
    """Converte o modelo ORM (coluna Geography) pro schema de resposta
    (lat/lon simples, arredondada) — é aqui que fica a tradução entre
    PostGIS e JSON.
    """
    point = to_shape(sighting.location)
    return SightingRead(
        id=sighting.id,
        reporter_id=sighting.reporter_id,
        description=sighting.description,
        status=sighting.status.value,
        latitude=round(point.y, PUBLIC_COORDINATE_PRECISION),
        longitude=round(point.x, PUBLIC_COORDINATE_PRECISION),
        created_at=sighting.created_at,
    )
