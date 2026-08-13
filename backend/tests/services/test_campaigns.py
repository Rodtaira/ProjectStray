import datetime as dt
import uuid
from decimal import Decimal

from app.models.campaign import CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.services import campaigns as campaigns_service


async def test_create_campaign_persists_with_the_creator_and_defaults(db_session, make_user):
    user = await make_user()
    data = CampaignCreate(title="Castração comunitária", goal_amount=Decimal("500.00"))

    campaign = await campaigns_service.create_campaign(db_session, data, created_by=user.id)

    assert campaign.id is not None
    assert campaign.created_by == user.id
    assert campaign.title == "Castração comunitária"
    assert campaign.goal_amount == Decimal("500.00")
    assert campaign.status == CampaignStatus.active
    assert campaign.animal_id is None


async def test_create_campaign_can_link_to_an_animal(db_session, make_user, make_animal):
    user = await make_user()
    animal = await make_animal(registered_by=user.id)
    data = CampaignCreate(
        title="Castração do Rex", goal_amount=Decimal("300.00"), animal_id=animal.id
    )

    campaign = await campaigns_service.create_campaign(db_session, data, created_by=user.id)

    assert campaign.animal_id == animal.id


async def test_get_campaign_by_id_returns_none_when_missing(db_session):
    assert await campaigns_service.get_campaign_by_id(db_session, uuid.uuid4()) is None


async def test_get_campaign_by_id_finds_an_existing_campaign(db_session, make_user, make_campaign):
    user = await make_user()
    campaign = await make_campaign(created_by=user.id)

    found = await campaigns_service.get_campaign_by_id(db_session, campaign.id)

    assert found is not None
    assert found.id == campaign.id


class TestListCampaigns:
    async def test_orders_by_most_recently_created_first(
        self, db_session, make_user, make_campaign
    ):
        user = await make_user()
        first = await make_campaign(
            created_by=user.id, created_at=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        )
        second = await make_campaign(
            created_by=user.id, created_at=dt.datetime(2026, 1, 2, tzinfo=dt.timezone.utc)
        )

        result = await campaigns_service.list_campaigns(db_session)

        ids_in_order = [c.id for c in result]
        assert ids_in_order.index(second.id) < ids_in_order.index(first.id)

    async def test_respects_the_limit(self, db_session, make_user, make_campaign):
        user = await make_user()
        for _ in range(3):
            await make_campaign(created_by=user.id)

        result = await campaigns_service.list_campaigns(db_session, limit=2)

        assert len(result) == 2


class TestUpdateCampaign:
    async def test_updates_only_the_provided_fields(self, db_session, make_user, make_campaign):
        user = await make_user()
        campaign = await make_campaign(
            created_by=user.id, title="Original", description="desc original"
        )

        updated = await campaigns_service.update_campaign(
            db_session, campaign, CampaignUpdate(title="Atualizado")
        )

        assert updated.title == "Atualizado"
        assert updated.description == "desc original"
        assert updated.status == CampaignStatus.active

    async def test_updates_the_status(self, db_session, make_user, make_campaign):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)

        updated = await campaigns_service.update_campaign(
            db_session, campaign, CampaignUpdate(status="cancelled")
        )

        assert updated.status == CampaignStatus.cancelled


def test_to_read_schema_maps_the_status_enum_to_its_plain_string():
    from app.models.campaign import Campaign

    campaign = Campaign(
        id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        animal_id=None,
        title="Campanha X",
        description=None,
        goal_amount=Decimal("100.00"),
        status=CampaignStatus.funded,
        created_at=dt.datetime.now(dt.timezone.utc),
    )

    schema = campaigns_service.to_read_schema(campaign)

    assert schema.status == "funded"
    assert schema.goal_amount == Decimal("100.00")
