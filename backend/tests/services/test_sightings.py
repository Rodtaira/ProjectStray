import datetime as dt
import uuid

from app.models.sighting import SightingStatus
from app.schemas.sighting import SightingCreate, SightingUpdate
from app.services import sightings as sightings_service


async def test_create_sighting_persists_the_reporter_and_location(db_session, make_user):
    user = await make_user()
    data = SightingCreate(description="cachorro caramelo", latitude=-15.7, longitude=-47.9)

    sighting = await sightings_service.create_sighting(db_session, data, reporter_id=user.id)

    assert sighting.id is not None
    assert sighting.reporter_id == user.id
    assert sighting.description == "cachorro caramelo"
    assert sighting.status == SightingStatus.open

    schema = sightings_service.to_read_schema(sighting)
    assert schema.latitude == -15.7
    assert schema.longitude == -47.9


async def test_get_sighting_by_id_returns_none_when_missing(db_session):
    assert await sightings_service.get_sighting_by_id(db_session, uuid.uuid4()) is None


async def test_get_sighting_by_id_finds_an_existing_sighting(db_session, make_user, make_sighting):
    user = await make_user()
    sighting = await make_sighting(reporter_id=user.id)

    found = await sightings_service.get_sighting_by_id(db_session, sighting.id)

    assert found is not None
    assert found.id == sighting.id


class TestListSightings:
    async def test_orders_by_most_recently_created_first(
        self, db_session, make_user, make_sighting
    ):
        user = await make_user()
        first = await make_sighting(
            reporter_id=user.id, created_at=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        )
        second = await make_sighting(
            reporter_id=user.id, created_at=dt.datetime(2026, 1, 2, tzinfo=dt.timezone.utc)
        )

        result = await sightings_service.list_sightings(db_session)

        ids_in_order = [s.id for s in result]
        assert ids_in_order.index(second.id) < ids_in_order.index(first.id)

    async def test_respects_the_limit(self, db_session, make_user, make_sighting):
        user = await make_user()
        for _ in range(3):
            await make_sighting(reporter_id=user.id)

        result = await sightings_service.list_sightings(db_session, limit=2)

        assert len(result) == 2


class TestUpdateSighting:
    async def test_updates_only_the_description(self, db_session, make_user, make_sighting):
        user = await make_user()
        sighting = await make_sighting(reporter_id=user.id, description="original")

        updated = await sightings_service.update_sighting(
            db_session, sighting, SightingUpdate(description="editada")
        )

        assert updated.description == "editada"
        assert updated.status == SightingStatus.open

    async def test_updates_only_the_status(self, db_session, make_user, make_sighting):
        user = await make_user()
        sighting = await make_sighting(reporter_id=user.id, description="original")

        updated = await sightings_service.update_sighting(
            db_session, sighting, SightingUpdate(status="resolved")
        )

        assert updated.status == SightingStatus.resolved
        assert updated.description == "original"


def test_to_read_schema_rounds_coordinates_to_public_precision():
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point

    from app.models.sighting import Sighting

    sighting = Sighting(
        id=uuid.uuid4(),
        reporter_id=uuid.uuid4(),
        description=None,
        status=SightingStatus.open,
        location=from_shape(Point(-47.912345, -15.799999), srid=4326),
        created_at=dt.datetime.now(dt.timezone.utc),
    )

    schema = sightings_service.to_read_schema(sighting)

    assert schema.latitude == -15.8
    assert schema.longitude == -47.912
