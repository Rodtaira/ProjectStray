import asyncio
import datetime as dt
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select

from app.models.campaign import Campaign, CampaignStatus
from app.models.donation import Donation, DonationStatus
from app.models.user import User, UserRole
from app.services import donations as donations_service


class TestCreateDonationWithCheckout:
    async def test_creates_a_pending_donation_and_returns_the_checkout_url(
        self, db_session, make_user, make_campaign, monkeypatch
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("200.00"))

        def fake_create_preference(**kwargs):
            assert kwargs["external_reference"]  # é preenchido com o id da doação recém-criada
            return {"id": "pref-123", "init_point": "https://checkout.mercadopago.com/pref-123"}

        monkeypatch.setattr(
            "app.services.payment_gateway.create_preference", fake_create_preference
        )

        donation, checkout_url = await donations_service.create_donation_with_checkout(
            db_session,
            campaign_id=campaign.id,
            campaign_title=campaign.title,
            amount=Decimal("50.00"),
            donor_id=user.id,
            success_url="https://api.example.com/callback",
        )

        assert donation.status == DonationStatus.pending
        assert donation.payment_reference == "pref-123"
        assert donation.campaign_id == campaign.id
        assert donation.donor_id == user.id
        assert checkout_url == "https://checkout.mercadopago.com/pref-123"

    async def test_uses_the_donation_id_as_the_external_reference(
        self, db_session, make_user, make_campaign, monkeypatch
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)
        captured = {}

        def fake_create_preference(**kwargs):
            captured["external_reference"] = kwargs["external_reference"]
            return {"id": "pref-456", "init_point": "https://checkout.example/pref-456"}

        monkeypatch.setattr(
            "app.services.payment_gateway.create_preference", fake_create_preference
        )

        donation, _ = await donations_service.create_donation_with_checkout(
            db_session,
            campaign_id=campaign.id,
            campaign_title=campaign.title,
            amount=Decimal("10.00"),
            donor_id=None,
            success_url="https://api.example.com/callback",
        )

        assert captured["external_reference"] == str(donation.id)

    async def test_translates_a_gateway_timeout_into_a_runtime_error(
        self, db_session, make_user, make_campaign, monkeypatch
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)

        async def fake_wait_for(coro, timeout):
            coro.close()  # evita o warning de "coroutine was never awaited"
            raise asyncio.TimeoutError()

        monkeypatch.setattr("app.services.donations.asyncio.wait_for", fake_wait_for)

        with pytest.raises(RuntimeError, match="Mercado Pago"):
            await donations_service.create_donation_with_checkout(
                db_session,
                campaign_id=campaign.id,
                campaign_title=campaign.title,
                amount=Decimal("10.00"),
                donor_id=user.id,
                success_url="https://api.example.com/callback",
            )


async def test_get_donation_by_id_returns_none_when_missing(db_session):
    assert await donations_service.get_donation_by_id(db_session, uuid.uuid4()) is None


async def test_get_donation_by_id_finds_an_existing_donation(
    db_session, make_user, make_campaign, make_donation
):
    user = await make_user()
    campaign = await make_campaign(created_by=user.id)
    donation = await make_donation(campaign_id=campaign.id)

    found = await donations_service.get_donation_by_id(db_session, donation.id)

    assert found is not None
    assert found.id == donation.id


class TestListDonations:
    async def test_only_returns_confirmed_donations(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)
        confirmed = await make_donation(campaign_id=campaign.id, status=DonationStatus.confirmed)
        await make_donation(campaign_id=campaign.id, status=DonationStatus.pending)
        await make_donation(campaign_id=campaign.id, status=DonationStatus.refunded)

        result = await donations_service.list_donations(db_session, campaign.id)

        assert [d.id for d in result] == [confirmed.id]

    async def test_orders_by_most_recently_created_first(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)
        first = await make_donation(
            campaign_id=campaign.id, created_at=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        )
        second = await make_donation(
            campaign_id=campaign.id, created_at=dt.datetime(2026, 1, 2, tzinfo=dt.timezone.utc)
        )

        result = await donations_service.list_donations(db_session, campaign.id)

        ids_in_order = [d.id for d in result]
        assert ids_in_order.index(second.id) < ids_in_order.index(first.id)

    async def test_respects_the_limit(self, db_session, make_user, make_campaign, make_donation):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)
        for _ in range(3):
            await make_donation(campaign_id=campaign.id)

        result = await donations_service.list_donations(db_session, campaign.id, limit=2)

        assert len(result) == 2

    async def test_does_not_leak_donations_from_other_campaigns(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign_a = await make_campaign(created_by=user.id)
        campaign_b = await make_campaign(created_by=user.id)
        donation_a = await make_donation(campaign_id=campaign_a.id)
        await make_donation(campaign_id=campaign_b.id)

        result = await donations_service.list_donations(db_session, campaign_a.id)

        assert [d.id for d in result] == [donation_a.id]


class TestConfirmDonation:
    async def test_marks_the_donation_as_confirmed(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("1000.00"))
        donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("10.00"), status=DonationStatus.pending
        )

        await donations_service.confirm_donation(db_session, donation)

        assert donation.status == DonationStatus.confirmed

    async def test_does_not_fund_the_campaign_below_goal(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("100.00"))
        donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("50.00"), status=DonationStatus.pending
        )

        await donations_service.confirm_donation(db_session, donation)

        assert campaign.status == CampaignStatus.active

    async def test_funds_the_campaign_once_the_goal_is_reached(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("100.00"))
        already_confirmed = await make_donation(
            campaign_id=campaign.id, amount=Decimal("60.00"), status=DonationStatus.confirmed
        )
        new_donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("40.00"), status=DonationStatus.pending
        )

        await donations_service.confirm_donation(db_session, new_donation)

        assert campaign.status == CampaignStatus.funded
        # Não mexe no que já tava confirmado.
        assert already_confirmed.status == DonationStatus.confirmed

    async def test_funds_the_campaign_when_it_goes_past_the_goal(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("100.00"))
        donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("150.00"), status=DonationStatus.pending
        )

        await donations_service.confirm_donation(db_session, donation)

        assert campaign.status == CampaignStatus.funded

    async def test_ignores_pending_and_refunded_donations_when_summing(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("100.00"))
        await make_donation(
            campaign_id=campaign.id, amount=Decimal("80.00"), status=DonationStatus.pending
        )
        await make_donation(
            campaign_id=campaign.id, amount=Decimal("80.00"), status=DonationStatus.refunded
        )
        donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("30.00"), status=DonationStatus.pending
        )

        await donations_service.confirm_donation(db_session, donation)

        # Só os 30 confirmados agora contam — os 80 pending/refunded não.
        assert campaign.status == CampaignStatus.active

    async def test_does_not_reopen_a_campaign_that_is_no_longer_active(
        self, db_session, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(
            created_by=user.id, goal_amount=Decimal("100.00"), status=CampaignStatus.cancelled
        )
        donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("500.00"), status=DonationStatus.pending
        )

        await donations_service.confirm_donation(db_session, donation)

        assert campaign.status == CampaignStatus.cancelled
        assert donation.status == DonationStatus.confirmed  # a doação em si ainda confirma


async def test_concurrent_confirmations_only_fund_the_campaign_once(raw_sessionmaker):
    """Regressão do race condition em _maybe_mark_campaign_funded: duas
    doações que só somam a meta JUNTAS, confirmadas ao mesmo tempo (webhook
    e callback correndo em paralelo, por exemplo), precisam terminar com a
    campanha 'funded' — sem o lock (FOR UPDATE), cada transação podia somar
    só a própria doação e nenhuma das duas veria o total combinado."""
    async with raw_sessionmaker() as setup_db:
        user = User(
            email=f"{uuid.uuid4()}@example.com", password_hash="x", role=UserRole.common
        )
        setup_db.add(user)
        await setup_db.flush()

        campaign = Campaign(
            created_by=user.id,
            title="Campanha concorrente",
            goal_amount=Decimal("100.00"),
            status=CampaignStatus.active,
        )
        setup_db.add(campaign)
        await setup_db.flush()

        donation_a = Donation(
            campaign_id=campaign.id,
            amount=Decimal("60.00"),
            payment_reference=f"a-{uuid.uuid4()}",
            status=DonationStatus.pending,
        )
        donation_b = Donation(
            campaign_id=campaign.id,
            amount=Decimal("60.00"),
            payment_reference=f"b-{uuid.uuid4()}",
            status=DonationStatus.pending,
        )
        setup_db.add_all([donation_a, donation_b])
        await setup_db.commit()

        campaign_id = campaign.id
        donation_ids = [donation_a.id, donation_b.id]
        user_id = user.id

    try:
        async def confirm(donation_id: uuid.UUID) -> None:
            async with raw_sessionmaker() as db:
                donation = (
                    await db.execute(select(Donation).where(Donation.id == donation_id))
                ).scalar_one()
                await donations_service.confirm_donation(db, donation)

        await asyncio.gather(*(confirm(donation_id) for donation_id in donation_ids))

        async with raw_sessionmaker() as db:
            campaign = (
                await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            ).scalar_one()
            assert campaign.status == CampaignStatus.funded
    finally:
        async with raw_sessionmaker() as db:
            await db.execute(delete(Donation).where(Donation.campaign_id == campaign_id))
            await db.execute(delete(Campaign).where(Campaign.id == campaign_id))
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()


def test_to_read_schema_maps_the_status_enum_to_its_plain_string():
    donation = Donation(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        donor_id=None,
        amount=Decimal("25.00"),
        payment_reference="pref-x",
        status=DonationStatus.confirmed,
        created_at=dt.datetime.now(dt.timezone.utc),
    )

    schema = donations_service.to_read_schema(donation)

    assert schema.status == "confirmed"
    assert schema.donor_id is None
