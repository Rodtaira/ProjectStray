import uuid
from decimal import Decimal

from app.models.donation import DonationStatus
from app.models.user import UserRole
from tests.conftest import as_user


class TestCreateCampaign:
    async def test_requires_authentication(self, client):
        response = await client.post(
            "/api/v1/campaigns", json={"title": "x", "goal_amount": "100.00"}
        )

        assert response.status_code == 401

    async def test_creates_a_campaign_owned_by_the_current_user(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            "/api/v1/campaigns", json={"title": "Castração", "goal_amount": "500.00"}
        )

        assert response.status_code == 201
        body = response.json()
        assert body["created_by"] == str(user.id)
        assert body["status"] == "active"

    async def test_rejects_a_non_positive_goal_amount(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            "/api/v1/campaigns", json={"title": "x", "goal_amount": "0.00"}
        )

        assert response.status_code == 422

    async def test_rejects_a_reference_to_an_animal_that_does_not_exist(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            "/api/v1/campaigns",
            json={"title": "x", "goal_amount": "100.00", "animal_id": str(uuid.uuid4())},
        )

        assert response.status_code == 404


class TestListCampaigns:
    async def test_does_not_require_authentication(self, client, make_user, make_campaign):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)

        response = await client.get("/api/v1/campaigns")

        assert response.status_code == 200
        ids = [c["id"] for c in response.json()]
        assert str(campaign.id) in ids


class TestGetCampaign:
    async def test_returns_404_for_a_missing_campaign(self, client):
        response = await client.get(f"/api/v1/campaigns/{uuid.uuid4()}")

        assert response.status_code == 404


class TestUpdateCampaign:
    async def test_the_owner_can_update_their_campaign(self, client, make_user, make_campaign):
        owner = await make_user()
        campaign = await make_campaign(created_by=owner.id, title="Original")
        as_user(owner)

        response = await client.patch(
            f"/api/v1/campaigns/{campaign.id}", json={"title": "Atualizada"}
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Atualizada"

    async def test_a_moderator_can_update_someone_elses_campaign(
        self, client, make_user, make_campaign
    ):
        owner = await make_user()
        moderator = await make_user(role=UserRole.moderator)
        campaign = await make_campaign(created_by=owner.id)
        as_user(moderator)

        response = await client.patch(
            f"/api/v1/campaigns/{campaign.id}", json={"status": "cancelled"}
        )

        assert response.status_code == 200

    async def test_a_stranger_cannot_update_someone_elses_campaign(
        self, client, make_user, make_campaign
    ):
        owner = await make_user()
        stranger = await make_user()
        campaign = await make_campaign(created_by=owner.id)
        as_user(stranger)

        response = await client.patch(
            f"/api/v1/campaigns/{campaign.id}", json={"title": "Hacked"}
        )

        assert response.status_code == 403


class TestCreateDonation:
    async def test_requires_authentication(self, client, make_user, make_campaign):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)

        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/donations", json={"amount": "10.00"}
        )

        assert response.status_code == 401

    async def test_returns_404_for_a_missing_campaign(self, client, make_user):
        user = await make_user()
        as_user(user)

        response = await client.post(
            f"/api/v1/campaigns/{uuid.uuid4()}/donations", json={"amount": "10.00"}
        )

        assert response.status_code == 404

    async def test_creates_a_pending_donation_and_returns_a_checkout_url(
        self, client, make_user, make_campaign, monkeypatch
    ):
        donor = await make_user()
        campaign = await make_campaign(created_by=donor.id, goal_amount=Decimal("1000.00"))
        as_user(donor)

        def fake_create_preference(**kwargs):
            return {"id": "pref-abc", "init_point": "https://checkout.example/pref-abc"}

        monkeypatch.setattr(
            "app.services.payment_gateway.create_preference", fake_create_preference
        )

        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/donations", json={"amount": "10.00"}
        )

        assert response.status_code == 201
        body = response.json()
        assert body["checkout_url"] == "https://checkout.example/pref-abc"
        assert body["donation"]["status"] == "pending"
        assert body["donation"]["donor_id"] == str(donor.id)


class TestListDonations:
    async def test_does_not_require_authentication(
        self, client, make_user, make_campaign, make_donation
    ):
        user = await make_user()
        campaign = await make_campaign(created_by=user.id)
        donation = await make_donation(campaign_id=campaign.id, status=DonationStatus.confirmed)
        await make_donation(campaign_id=campaign.id, status=DonationStatus.pending)

        response = await client.get(f"/api/v1/campaigns/{campaign.id}/donations")

        assert response.status_code == 200
        ids = [d["id"] for d in response.json()]
        assert ids == [str(donation.id)]
