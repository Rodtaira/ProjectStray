import hashlib
import hmac
from decimal import Decimal

from app.models.campaign import CampaignStatus
from app.models.donation import DonationStatus


def _sign(secret: str, data_id: str, ts: str, request_id: str) -> str:
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


def _signed_headers(secret: str, data_id: str) -> dict:
    ts = "1700000000"
    request_id = "req-abc"
    v1 = _sign(secret, data_id, ts, request_id)
    return {"x-signature": f"ts={ts},v1={v1}", "x-request-id": request_id}


class TestMercadoPagoWebhook:
    async def test_rejects_an_invalid_signature(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        response = await client.post(
            "/api/v1/webhooks/payments/mercadopago",
            params={"data.id": "pay-1"},
            headers={"x-signature": "ts=1,v1=deadbeef", "x-request-id": "req-abc"},
            json={"type": "payment", "data": {"id": "pay-1"}},
        )

        assert response.status_code == 401

    async def test_ignores_notifications_that_are_not_payments(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        headers = _signed_headers("test-secret", "merchant-order-1")

        response = await client.post(
            "/api/v1/webhooks/payments/mercadopago",
            params={"data.id": "merchant-order-1"},
            headers=headers,
            json={"type": "merchant_order", "data": {"id": "merchant-order-1"}},
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    async def test_confirms_the_donation_when_the_payment_is_approved(
        self, client, make_user, make_campaign, make_donation, monkeypatch
    ):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        user = await make_user()
        campaign = await make_campaign(created_by=user.id, goal_amount=Decimal("1000.00"))
        donation = await make_donation(
            campaign_id=campaign.id, amount=Decimal("10.00"), status=DonationStatus.pending
        )

        def fake_get_payment(payment_id):
            return {"status": "approved", "external_reference": str(donation.id)}

        monkeypatch.setattr(
            "app.services.payment_gateway.get_payment", fake_get_payment
        )
        headers = _signed_headers("test-secret", "pay-1")

        response = await client.post(
            "/api/v1/webhooks/payments/mercadopago",
            params={"data.id": "pay-1"},
            headers=headers,
            json={"type": "payment", "data": {"id": "pay-1"}},
        )

        assert response.status_code == 200
        # Mesma sessão de teste é usada pela rota (via override de get_db),
        # então o objeto `donation` já reflete o commit feito dentro dela.
        assert donation.status == DonationStatus.confirmed
        assert campaign.status == CampaignStatus.active  # 10,00 não bate a meta de 1000,00

    async def test_does_not_crash_on_an_unknown_external_reference(
        self, client, monkeypatch
    ):
        import uuid

        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        def fake_get_payment(payment_id):
            return {"status": "approved", "external_reference": str(uuid.uuid4())}

        monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)
        headers = _signed_headers("test-secret", "pay-2")

        response = await client.post(
            "/api/v1/webhooks/payments/mercadopago",
            params={"data.id": "pay-2"},
            headers=headers,
            json={"type": "payment", "data": {"id": "pay-2"}},
        )

        assert response.status_code == 200

    async def test_does_not_crash_when_external_reference_is_not_a_uuid(
        self, client, monkeypatch
    ):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        def fake_get_payment(payment_id):
            return {"status": "approved", "external_reference": "not-a-uuid"}

        monkeypatch.setattr("app.services.payment_gateway.get_payment", fake_get_payment)
        headers = _signed_headers("test-secret", "pay-3")

        response = await client.post(
            "/api/v1/webhooks/payments/mercadopago",
            params={"data.id": "pay-3"},
            headers=headers,
            json={"type": "payment", "data": {"id": "pay-3"}},
        )

        assert response.status_code == 200
