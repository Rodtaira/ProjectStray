import uuid
from decimal import Decimal

from app.models.campaign import CampaignStatus
from app.models.donation import DonationStatus


async def test_reports_processed_but_unconfirmed_when_no_query_params_are_given(client):
    response = await client.get("/api/v1/donations/callback")

    assert response.status_code == 200
    assert "Pagamento processado" in response.text


async def test_reports_processed_but_unconfirmed_when_external_reference_is_not_a_uuid(
    client, monkeypatch
):
    def fake_get_payment(payment_id):
        return {"status": "approved"}

    monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)

    response = await client.get(
        "/api/v1/donations/callback",
        params={"payment_id": "pay-1", "external_reference": "not-a-uuid"},
    )

    assert response.status_code == 200
    assert "Pagamento processado" in response.text


async def test_reports_processed_but_unconfirmed_when_the_payment_is_not_approved(
    client, make_user, make_campaign, make_donation, monkeypatch
):
    user = await make_user()
    campaign = await make_campaign(created_by=user.id)
    donation = await make_donation(campaign_id=campaign.id, status=DonationStatus.pending)

    def fake_get_payment(payment_id):
        return {"status": "pending"}

    monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)

    response = await client.get(
        "/api/v1/donations/callback",
        params={"payment_id": "pay-1", "external_reference": str(donation.id)},
    )

    assert response.status_code == 200
    assert "Pagamento processado" in response.text
    assert donation.status == DonationStatus.pending


async def test_confirms_the_donation_when_the_payment_is_approved(
    client, make_user, make_campaign, make_donation, monkeypatch
):
    user = await make_user()
    campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("1000.00"))
    donation = await make_donation(
        campaign_id=campaign.id, amount=Decimal("10.00"), status=DonationStatus.pending
    )

    def fake_get_payment(payment_id):
        return {"status": "approved"}

    monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)

    response = await client.get(
        "/api/v1/donations/callback",
        params={"payment_id": "pay-1", "external_reference": str(donation.id)},
    )

    assert response.status_code == 200
    assert "Pagamento confirmado" in response.text
    assert donation.status == DonationStatus.confirmed
    assert campaign.status == CampaignStatus.active  # 10,00 não bate a meta de 1000,00


async def test_does_not_crash_when_the_donation_does_not_exist(client, monkeypatch):
    def fake_get_payment(payment_id):
        return {"status": "approved"}

    monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)

    response = await client.get(
        "/api/v1/donations/callback",
        params={"payment_id": "pay-1", "external_reference": str(uuid.uuid4())},
    )

    assert response.status_code == 200
    # A busca no MP confirmou o pagamento; só não achamos a doação pra marcar.
    assert "Pagamento confirmado" in response.text


async def test_does_not_crash_when_the_gateway_lookup_fails(
    client, make_user, make_campaign, make_donation, monkeypatch
):
    user = await make_user()
    campaign = await make_campaign(created_by=user.id)
    donation = await make_donation(campaign_id=campaign.id, status=DonationStatus.pending)

    def fake_get_payment(payment_id):
        raise RuntimeError("Mercado Pago está fora do ar")

    monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)

    response = await client.get(
        "/api/v1/donations/callback",
        params={"payment_id": "pay-1", "external_reference": str(donation.id)},
    )

    assert response.status_code == 200
    assert "Pagamento processado" in response.text
    assert donation.status == DonationStatus.pending
