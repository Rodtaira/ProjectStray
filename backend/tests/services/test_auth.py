import datetime as dt

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.services import auth as auth_service


class TestPasswordHashing:
    def test_hash_is_not_the_plaintext_password(self):
        hashed = auth_service.hash_password("hunter22")

        assert hashed != "hunter22"

    def test_verify_password_accepts_the_correct_password(self):
        hashed = auth_service.hash_password("hunter22")

        assert auth_service.verify_password("hunter22", hashed) is True

    def test_verify_password_rejects_the_wrong_password(self):
        hashed = auth_service.hash_password("hunter22")

        assert auth_service.verify_password("wrong-password", hashed) is False

    def test_hashing_the_same_password_twice_yields_different_hashes(self):
        # bcrypt salga cada hash — isso é o que impede um "rainbow table"
        # de funcionar contra a base, mesmo se duas contas usarem a mesma senha.
        assert auth_service.hash_password("hunter22") != auth_service.hash_password("hunter22")


class TestTokens:
    def test_access_token_round_trips_to_the_user_id(self):
        token = auth_service.create_access_token("user-123")

        assert auth_service.decode_token(token, expected_type="access") == "user-123"

    def test_refresh_token_round_trips_to_the_user_id(self):
        token = auth_service.create_refresh_token("user-123")

        assert auth_service.decode_token(token, expected_type="refresh") == "user-123"

    def test_an_access_token_is_rejected_when_a_refresh_token_is_expected(self):
        token = auth_service.create_access_token("user-123")

        with pytest.raises(JWTError):
            auth_service.decode_token(token, expected_type="refresh")

    def test_a_refresh_token_is_rejected_when_an_access_token_is_expected(self):
        token = auth_service.create_refresh_token("user-123")

        with pytest.raises(JWTError):
            auth_service.decode_token(token, expected_type="access")

    def test_an_expired_token_is_rejected(self):
        expired_payload = {
            "sub": "user-123",
            "type": "access",
            "exp": dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(JWTError):
            auth_service.decode_token(expired_token, expected_type="access")

    def test_a_token_signed_with_the_wrong_secret_is_rejected(self):
        forged = jwt.encode(
            {
                "sub": "user-123",
                "type": "access",
                "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5),
            },
            "not-the-real-secret",
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(JWTError):
            auth_service.decode_token(forged, expected_type="access")


class TestUserLookups:
    async def test_get_user_by_email_finds_an_existing_user(self, db_session, make_user):
        user = await make_user(email="lookup@example.com")

        found = await auth_service.get_user_by_email(db_session, "lookup@example.com")

        assert found is not None
        assert found.id == user.id

    async def test_get_user_by_email_returns_none_when_not_found(self, db_session):
        found = await auth_service.get_user_by_email(db_session, "nobody@example.com")

        assert found is None

    async def test_get_user_by_id_finds_an_existing_user(self, db_session, make_user):
        user = await make_user()

        found = await auth_service.get_user_by_id(db_session, str(user.id))

        assert found is not None
        assert found.email == user.email

    async def test_register_user_persists_a_hashed_password(self, db_session):
        user = await auth_service.register_user(
            db_session,
            email="new@example.com",
            password="hunter22",
            full_name="Nova Pessoa",
            phone=None,
        )

        assert user.id is not None
        assert user.password_hash != "hunter22"
        assert auth_service.verify_password("hunter22", user.password_hash) is True
