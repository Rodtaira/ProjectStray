import uuid

from app.models.user import UserRole
from tests.conftest import as_user


class TestCreateSighting:
    async def test_requires_authentication(self, client):
        response = await client.post(
            "/api/v1/sightings", json={"latitude": -15.7, "longitude": -47.9}
        )

        assert response.status_code == 401

    async def test_creates_a_sighting_reported_by_the_current_user(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            "/api/v1/sightings",
            json={"description": "cachorro caramelo", "latitude": -15.7, "longitude": -47.9},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["reporter_id"] == str(user.id)
        assert body["status"] == "open"

    async def test_rejects_an_out_of_range_latitude(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            "/api/v1/sightings", json={"latitude": 999, "longitude": -47.9}
        )

        assert response.status_code == 422


class TestListSightings:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/sightings")

        assert response.status_code == 401

    async def test_returns_the_created_sightings(self, client, make_user, make_sighting):
        user = await make_user()
        as_user(user)
        sighting = await make_sighting(reporter_id=user.id)

        response = await client.get("/api/v1/sightings")

        assert response.status_code == 200
        ids = [s["id"] for s in response.json()]
        assert str(sighting.id) in ids


class TestGetSighting:
    async def test_returns_404_for_a_missing_sighting(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.get(f"/api/v1/sightings/{uuid.uuid4()}")

        assert response.status_code == 404


class TestUpdateSighting:
    async def test_the_reporter_can_update_their_sighting(self, client, make_user, make_sighting):
        reporter = await make_user()
        sighting = await make_sighting(reporter_id=reporter.id)
        as_user(reporter)

        response = await client.patch(
            f"/api/v1/sightings/{sighting.id}", json={"status": "resolved"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    async def test_a_moderator_can_update_someone_elses_sighting(
        self, client, make_user, make_sighting
    ):
        reporter = await make_user()
        moderator = await make_user(role=UserRole.moderator)
        sighting = await make_sighting(reporter_id=reporter.id)
        as_user(moderator)

        response = await client.patch(
            f"/api/v1/sightings/{sighting.id}", json={"status": "resolved"}
        )

        assert response.status_code == 200

    async def test_a_stranger_cannot_update_someone_elses_sighting(
        self, client, make_user, make_sighting
    ):
        reporter = await make_user()
        stranger = await make_user()
        sighting = await make_sighting(reporter_id=reporter.id)
        as_user(stranger)

        response = await client.patch(
            f"/api/v1/sightings/{sighting.id}", json={"status": "resolved"}
        )

        assert response.status_code == 403

    async def test_returns_404_for_a_missing_sighting(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.patch(
            f"/api/v1/sightings/{uuid.uuid4()}", json={"status": "resolved"}
        )

        assert response.status_code == 404


async def test_matches_endpoint_is_not_implemented_yet(client, make_user, make_sighting):
    user = await make_user()
    sighting = await make_sighting(reporter_id=user.id)
    as_user(user)

    response = await client.get(f"/api/v1/sightings/{sighting.id}/matches")

    assert response.status_code == 501
