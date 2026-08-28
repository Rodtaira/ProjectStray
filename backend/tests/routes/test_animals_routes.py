import uuid

from app.models.user import UserRole
from tests.conftest import as_user


class TestCreateAnimal:
    async def test_requires_authentication(self, client):
        response = await client.post("/api/v1/animals", json={"species": "dog"})

        assert response.status_code == 401

    async def test_creates_an_animal_owned_by_the_current_user(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post("/api/v1/animals", json={"species": "dog", "name": "Rex"})

        assert response.status_code == 201
        body = response.json()
        assert body["registered_by"] == str(user.id)
        assert body["name"] == "Rex"


class TestListAnimals:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/animals")

        assert response.status_code == 401

    async def test_filters_by_species_query_param(self, client, make_user, make_animal):
        from app.models.animal import AnimalSpecies

        user = await make_user()
        as_user(user)
        dog = await make_animal(registered_by=user.id, species=AnimalSpecies.dog)
        await make_animal(registered_by=user.id, species=AnimalSpecies.cat)

        response = await client.get("/api/v1/animals", params={"species": "dog"})

        assert response.status_code == 200
        ids = [a["id"] for a in response.json()]
        assert ids == [str(dog.id)]

    async def test_rejects_an_invalid_species_value(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.get("/api/v1/animals", params={"species": "dragon"})

        assert response.status_code == 422


class TestGetAnimal:
    async def test_returns_404_for_a_missing_animal(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.get(f"/api/v1/animals/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_returns_the_animal_when_it_exists(self, client, make_user, make_animal):
        user = await make_user()
        as_user(user)
        animal = await make_animal(registered_by=user.id, name="Rex")

        response = await client.get(f"/api/v1/animals/{animal.id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Rex"


class TestUpdateAnimal:
    async def test_the_owner_can_update_their_animal(self, client, make_user, make_animal):
        owner = await make_user()
        animal = await make_animal(registered_by=owner.id, name="Rex")
        as_user(owner)

        response = await client.patch(f"/api/v1/animals/{animal.id}", json={"name": "Rex II"})

        assert response.status_code == 200
        assert response.json()["name"] == "Rex II"

    async def test_a_moderator_can_update_someone_elses_animal(
        self, client, make_user, make_animal
    ):
        owner = await make_user()
        moderator = await make_user(role=UserRole.moderator)
        animal = await make_animal(registered_by=owner.id, name="Rex")
        as_user(moderator)

        response = await client.patch(f"/api/v1/animals/{animal.id}", json={"name": "Rex II"})

        assert response.status_code == 200

    async def test_a_stranger_cannot_update_someone_elses_animal(
        self, client, make_user, make_animal
    ):
        owner = await make_user()
        stranger = await make_user()
        animal = await make_animal(registered_by=owner.id, name="Rex")
        as_user(stranger)

        response = await client.patch(f"/api/v1/animals/{animal.id}", json={"name": "Hacked"})

        assert response.status_code == 403

    async def test_returns_404_for_a_missing_animal(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.patch(f"/api/v1/animals/{uuid.uuid4()}", json={"name": "x"})

        assert response.status_code == 404


class TestDeleteAnimal:
    async def test_the_owner_can_delete_their_animal(self, client, make_user, make_animal):
        owner = await make_user()
        animal = await make_animal(registered_by=owner.id)
        as_user(owner)

        response = await client.delete(f"/api/v1/animals/{animal.id}")

        assert response.status_code == 204

    async def test_a_stranger_cannot_delete_someone_elses_animal(
        self, client, make_user, make_animal
    ):
        owner = await make_user()
        stranger = await make_user()
        animal = await make_animal(registered_by=owner.id)
        as_user(stranger)

        response = await client.delete(f"/api/v1/animals/{animal.id}")

        assert response.status_code == 403

    async def test_a_moderator_can_delete_someone_elses_animal(
        self, client, make_user, make_animal
    ):
        owner = await make_user()
        moderator = await make_user(role=UserRole.moderator)
        animal = await make_animal(registered_by=owner.id)
        as_user(moderator)

        response = await client.delete(f"/api/v1/animals/{animal.id}")

        assert response.status_code == 204


import io

from PIL import Image

from app.services import storage


def _make_jpeg_bytes(width: int = 10, height: int = 10) -> bytes:
    image = Image.new("RGB", (width, height), color="green")
    output = io.BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


class TestUploadAnimalPhoto:
    async def test_requires_authentication(self, client, make_user, make_animal):
        owner = await make_user()
        animal = await make_animal(registered_by=owner.id)

        response = await client.post(
            f"/api/v1/animals/{animal.id}/photo",
            files={"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

        assert response.status_code == 401

    async def test_the_owner_can_upload_a_photo(self, client, make_user, make_animal, monkeypatch):
        monkeypatch.setattr(storage, "upload_bytes", lambda key, data, content_type: None)
        owner = await make_user()
        animal = await make_animal(registered_by=owner.id)
        as_user(owner)

        response = await client.post(
            f"/api/v1/animals/{animal.id}/photo",
            files={"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

        assert response.status_code == 200
        assert response.json()["photo_url"] == f"/api/v1/animals/{animal.id}/photo"

    async def test_a_moderator_can_upload_a_photo_for_someone_elses_animal(
        self, client, make_user, make_animal, monkeypatch
    ):
        monkeypatch.setattr(storage, "upload_bytes", lambda key, data, content_type: None)
        owner = await make_user()
        moderator = await make_user(role=UserRole.moderator)
        animal = await make_animal(registered_by=owner.id)
        as_user(moderator)

        response = await client.post(
            f"/api/v1/animals/{animal.id}/photo",
            files={"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

        assert response.status_code == 200

    async def test_a_stranger_cannot_upload_a_photo_for_someone_elses_animal(
        self, client, make_user, make_animal
    ):
        owner = await make_user()
        stranger = await make_user()
        animal = await make_animal(registered_by=owner.id)
        as_user(stranger)

        response = await client.post(
            f"/api/v1/animals/{animal.id}/photo",
            files={"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

        assert response.status_code == 403

    async def test_returns_404_for_a_missing_animal(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            f"/api/v1/animals/{uuid.uuid4()}/photo",
            files={"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

        assert response.status_code == 404

    async def test_rejects_a_non_image_content_type(self, client, make_user, make_animal):
        owner = await make_user()
        animal = await make_animal(registered_by=owner.id)
        as_user(owner)

        response = await client.post(
            f"/api/v1/animals/{animal.id}/photo",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )

        assert response.status_code == 415

    async def test_rejects_a_file_larger_than_8mb(self, client, make_user, make_animal):
        owner = await make_user()
        animal = await make_animal(registered_by=owner.id)
        as_user(owner)

        oversized = b"x" * (8 * 1024 * 1024 + 1)

        response = await client.post(
            f"/api/v1/animals/{animal.id}/photo",
            files={"file": ("big.jpg", oversized, "image/jpeg")},
        )

        assert response.status_code == 413
