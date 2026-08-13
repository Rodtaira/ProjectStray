import uuid
from decimal import Decimal
from typing import AsyncIterator

import pytest_asyncio
from geoalchemy2.shape import from_shape
from httpx import ASGITransport, AsyncClient
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.main import app
from app.models import Animal, Campaign, Donation, Sighting, User  # noqa: F401 -- registra as tabelas
from app.models.animal import AnimalSex, AnimalSpecies, AnimalStatus
from app.models.base import Base
from app.models.campaign import CampaignStatus
from app.models.donation import DonationStatus
from app.models.sighting import SightingStatus
from app.models.user import UserRole
from app.services import auth as auth_service

# Banco isolado do de desenvolvimento — mesmo cluster Postgres, database
# separado (ver `docker compose exec db psql -c "CREATE DATABASE app_db_test"`
# nas notas de setup). Nunca aponta pro app_db real.
TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/app_db_test"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
def raw_sessionmaker(engine):
    """Sessions com conexão própria e commit de verdade — só pra testes que
    precisam simular transações concorrentes reais (ver
    test_donations.py::test_concurrent_confirmations_only_fund_the_campaign_once).
    A maioria dos testes deve usar `db_session`, não isso."""
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    """Uma sessão por teste, dentro de uma transação externa que é sempre
    revertida no final — isola os testes entre si sem precisar recriar o
    schema a cada um. `db.commit()` dentro do código de produção não
    escapa dessa transação: vira um savepoint (join_transaction_mode)."""
    connection = await engine.connect()
    trans = await connection.begin()
    session_maker = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = session_maker()
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP contra a app real, com o banco trocado pela sessão de
    teste. Autenticação continua exigindo override explícito de
    get_current_user em cada teste que precisar (ver fixture `as_user`)."""

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def as_user(user: User):
    """Faz `client` autenticar como `user` sem precisar gerar/validar um
    JWT de verdade — substitui a dependency get_current_user direto."""

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


# --- factories -------------------------------------------------------------


@pytest_asyncio.fixture
def make_user(db_session):
    async def _make(
        email: str | None = None,
        role: UserRole = UserRole.common,
        password: str = "hunter22",
        **kwargs,
    ) -> User:
        user = User(
            email=email or f"{uuid.uuid4()}@example.com",
            password_hash=auth_service.hash_password(password),
            role=role,
            **kwargs,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    return _make


@pytest_asyncio.fixture
def make_animal(db_session):
    async def _make(registered_by: uuid.UUID, **kwargs) -> Animal:
        animal = Animal(
            registered_by=registered_by,
            species=kwargs.pop("species", AnimalSpecies.dog),
            sex=kwargs.pop("sex", AnimalSex.unknown),
            status=kwargs.pop("status", AnimalStatus.stray),
            **kwargs,
        )
        db_session.add(animal)
        await db_session.flush()
        return animal

    return _make


@pytest_asyncio.fixture
def make_sighting(db_session):
    async def _make(
        reporter_id: uuid.UUID,
        latitude: float = -15.7,
        longitude: float = -47.9,
        status: SightingStatus = SightingStatus.open,
        **kwargs,
    ) -> Sighting:
        sighting = Sighting(
            reporter_id=reporter_id,
            location=from_shape(Point(longitude, latitude), srid=4326),
            status=status,
            **kwargs,
        )
        db_session.add(sighting)
        await db_session.flush()
        return sighting

    return _make


@pytest_asyncio.fixture
def make_campaign(db_session):
    async def _make(
        created_by: uuid.UUID,
        goal_amount: Decimal = Decimal("100.00"),
        status: CampaignStatus = CampaignStatus.active,
        title: str = "Castração da comunidade X",
        **kwargs,
    ) -> Campaign:
        campaign = Campaign(
            created_by=created_by,
            title=title,
            goal_amount=goal_amount,
            status=status,
            **kwargs,
        )
        db_session.add(campaign)
        await db_session.flush()
        return campaign

    return _make


@pytest_asyncio.fixture
def make_donation(db_session):
    async def _make(
        campaign_id: uuid.UUID,
        amount: Decimal = Decimal("50.00"),
        status: DonationStatus = DonationStatus.confirmed,
        donor_id: uuid.UUID | None = None,
        payment_reference: str | None = None,
        **kwargs,
    ) -> Donation:
        donation = Donation(
            campaign_id=campaign_id,
            donor_id=donor_id,
            amount=amount,
            status=status,
            payment_reference=payment_reference or f"pref-{uuid.uuid4()}",
            **kwargs,
        )
        db_session.add(donation)
        await db_session.flush()
        return donation

    return _make
