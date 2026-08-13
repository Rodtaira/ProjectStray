from app.models.user import UserRole
from app.services import auth as auth_service


class TestRegister:
    async def test_registers_a_new_user_and_returns_usable_tokens(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "nova@example.com", "password": "hunter22", "full_name": "Nova"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["token_type"] == "bearer"
        assert auth_service.decode_token(body["access_token"], expected_type="access")
        assert auth_service.decode_token(body["refresh_token"], expected_type="refresh")

    async def test_rejects_a_duplicate_email(self, client, make_user):
        await make_user(email="dup@example.com")

        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "hunter22"},
        )

        assert response.status_code == 409

    async def test_rejects_a_password_shorter_than_8_characters(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "1234567"},
        )

        assert response.status_code == 422


class TestLogin:
    async def test_logs_in_with_the_correct_credentials(self, client, make_user):
        await make_user(email="login@example.com", password="hunter22")

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "hunter22"},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_rejects_the_wrong_password(self, client, make_user):
        await make_user(email="login2@example.com", password="hunter22")

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login2@example.com", "password": "wrong-password"},
        )

        assert response.status_code == 401

    async def test_rejects_an_email_that_does_not_exist(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "whatever1"},
        )

        assert response.status_code == 401

    async def test_rejects_a_soft_deleted_user(self, client, make_user):
        import datetime as dt

        await make_user(
            email="deleted@example.com",
            password="hunter22",
            deleted_at=dt.datetime.now(dt.timezone.utc),
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "deleted@example.com", "password": "hunter22"},
        )

        assert response.status_code == 401


class TestRefresh:
    async def test_issues_a_new_token_pair_from_a_valid_refresh_token(self, client, make_user):
        user = await make_user()
        refresh_token = auth_service.create_refresh_token(str(user.id))

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        body = response.json()
        new_user_id = auth_service.decode_token(body["access_token"], expected_type="access")
        assert new_user_id == str(user.id)

    async def test_rejects_an_access_token_used_as_a_refresh_token(self, client, make_user):
        user = await make_user()
        access_token = auth_service.create_access_token(str(user.id))

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

        assert response.status_code == 401

    async def test_rejects_a_garbage_token(self, client):
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
        )

        assert response.status_code == 401

    async def test_rejects_a_refresh_token_for_a_user_that_no_longer_exists(self, client):
        import uuid

        refresh_token = auth_service.create_refresh_token(str(uuid.uuid4()))

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 401


class TestGetCurrentUserDependency:
    """Exercita a cadeia de autenticação de verdade (header -> JWT -> DB),
    via um endpoint protegido qualquer — /users/me é o mais simples."""

    async def test_rejects_a_request_without_a_token(self, client):
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_rejects_an_invalid_token(self, client):
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer garbage"}
        )

        assert response.status_code == 401

    async def test_accepts_a_valid_access_token(self, client, make_user):
        user = await make_user(email="me@example.com", role=UserRole.common)
        token = auth_service.create_access_token(str(user.id))

        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    async def test_rejects_a_refresh_token_used_as_an_access_token(self, client, make_user):
        user = await make_user()
        refresh_token = auth_service.create_refresh_token(str(user.id))

        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {refresh_token}"}
        )

        assert response.status_code == 401
