import datetime as dt
import uuid

from tests.conftest import as_user


class TestGetUserPublic:
    async def test_requires_authentication(self, client, make_user):
        target = await make_user()

        response = await client.get(f"/api/v1/users/{target.id}")

        assert response.status_code == 401

    async def test_returns_the_public_profile_without_email_or_phone(self, client, make_user):
        viewer = await make_user()
        target = await make_user(full_name="Fulano", phone="11999999999")
        as_user(viewer)

        response = await client.get(f"/api/v1/users/{target.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["full_name"] == "Fulano"
        assert "email" not in body
        assert "phone" not in body

    async def test_returns_404_for_a_missing_user(self, client, make_user):
        viewer = await make_user()
        as_user(viewer)

        response = await client.get(f"/api/v1/users/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_returns_404_for_a_soft_deleted_user(self, client, make_user):
        viewer = await make_user()
        target = await make_user(deleted_at=dt.datetime.now(dt.timezone.utc))
        as_user(viewer)

        response = await client.get(f"/api/v1/users/{target.id}")

        assert response.status_code == 404
