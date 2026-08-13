import uuid

import pytest

from app.models.user import UserRole
from tests.conftest import as_user

# Endpoints planejados mas ainda não implementados — todos devolvem 501
# quando autenticados. Esse sweep é barato e garante duas coisas ao mesmo
# tempo: que a autenticação continua sendo exigida, e que "não implementado"
# continua sendo "não implementado" até alguém decidir implementar de verdade
# (nesse ponto o teste abaixo vai falhar e servir de lembrete pra escrever
# a cobertura de verdade).
SIMPLE_STUBS = [
    ("POST", "/api/v1/conversations"),
    ("GET", "/api/v1/conversations"),
    ("GET", f"/api/v1/conversations/{uuid.uuid4()}/messages"),
    ("POST", f"/api/v1/conversations/{uuid.uuid4()}/read"),
    ("POST", "/api/v1/feeding-points"),
    ("GET", "/api/v1/feeding-points"),
    ("PATCH", f"/api/v1/feeding-points/{uuid.uuid4()}"),
    ("POST", "/api/v1/media/upload-url"),
    ("POST", f"/api/v1/media/{uuid.uuid4()}/confirm"),
    (
        "POST",
        f"/api/v1/matches/{uuid.uuid4()}/confirm",
    ),
    ("POST", f"/api/v1/matches/{uuid.uuid4()}/reject"),
    ("POST", "/api/v1/flags"),
    ("PATCH", "/api/v1/users/me"),
    ("DELETE", "/api/v1/users/me"),
]


@pytest.mark.parametrize("method,path", SIMPLE_STUBS)
async def test_requires_authentication(client, method, path):
    response = await client.request(method, path)

    assert response.status_code == 401


@pytest.mark.parametrize("method,path", SIMPLE_STUBS)
async def test_returns_not_implemented_once_authenticated(client, make_user, method, path):
    user = await make_user()
    as_user(user)

    response = await client.request(method, path)

    assert response.status_code == 501


MODERATOR_ONLY_STUBS = [
    ("GET", "/api/v1/moderation/queue"),
    ("POST", "/api/v1/moderation/actions"),
    ("GET", "/api/v1/moderation/actions"),
]


@pytest.mark.parametrize("method,path", MODERATOR_ONLY_STUBS)
async def test_moderation_endpoints_require_authentication(client, method, path):
    response = await client.request(method, path)

    assert response.status_code == 401


@pytest.mark.parametrize("method,path", MODERATOR_ONLY_STUBS)
async def test_moderation_endpoints_reject_a_common_user(client, make_user, method, path):
    user = await make_user(role=UserRole.common)
    as_user(user)

    response = await client.request(method, path)

    assert response.status_code == 403


@pytest.mark.parametrize("method,path", MODERATOR_ONLY_STUBS)
async def test_moderation_endpoints_return_not_implemented_for_a_moderator(
    client, make_user, method, path
):
    moderator = await make_user(role=UserRole.moderator)
    as_user(moderator)

    response = await client.request(method, path)

    assert response.status_code == 501
