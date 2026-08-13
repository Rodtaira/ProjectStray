import pytest

from app.services import payment_gateway


class FakePreferenceClient:
    def __init__(self, response):
        self._response = response

    def create(self, data):
        self.last_call = data
        return {"response": self._response}


class FakePaymentClient:
    def __init__(self, response):
        self._response = response

    def get(self, payment_id):
        self.last_call = payment_id
        return {"response": self._response}


class FakeSDK:
    def __init__(self, preference_response=None, payment_response=None):
        self._preference_client = FakePreferenceClient(preference_response or {})
        self._payment_client = FakePaymentClient(payment_response or {})

    def preference(self):
        return self._preference_client

    def payment(self):
        return self._payment_client


class TestCreatePreference:
    def test_returns_the_gateway_response_when_it_succeeds(self, monkeypatch):
        fake_sdk = FakeSDK(
            preference_response={"id": "pref-123", "init_point": "https://checkout/pref-123"}
        )
        monkeypatch.setattr(payment_gateway, "_sdk", fake_sdk)

        result = payment_gateway.create_preference(
            title="Doação - Campanha X",
            amount=42.5,
            external_reference="donation-1",
            success_url="https://api.example.com/callback",
        )

        assert result["id"] == "pref-123"
        assert result["init_point"] == "https://checkout/pref-123"

    def test_sends_a_single_item_with_the_given_title_and_amount(self, monkeypatch):
        fake_sdk = FakeSDK(preference_response={"id": "pref-123", "init_point": "url"})
        monkeypatch.setattr(payment_gateway, "_sdk", fake_sdk)

        payment_gateway.create_preference(
            title="Doação - Campanha X",
            amount=42.5,
            external_reference="donation-1",
            success_url="https://api.example.com/callback",
        )

        sent = fake_sdk._preference_client.last_call
        assert sent["items"] == [
            {
                "title": "Doação - Campanha X",
                "quantity": 1,
                "unit_price": 42.5,
                "currency_id": "BRL",
            }
        ]
        assert sent["external_reference"] == "donation-1"

    def test_does_not_send_a_notification_url(self, monkeypatch):
        # Documentado no código de produção: notification_url na criação
        # sobrescreveria a configurada no painel, que é a única assinada.
        fake_sdk = FakeSDK(preference_response={"id": "pref-123", "init_point": "url"})
        monkeypatch.setattr(payment_gateway, "_sdk", fake_sdk)

        payment_gateway.create_preference(
            title="x", amount=1.0, external_reference="d1", success_url="https://x.example/cb"
        )

        assert "notification_url" not in fake_sdk._preference_client.last_call

    def test_raises_when_the_gateway_refuses_the_preference(self, monkeypatch):
        fake_sdk = FakeSDK(preference_response={"status": "error", "message": "invalid token"})
        monkeypatch.setattr(payment_gateway, "_sdk", fake_sdk)

        with pytest.raises(RuntimeError, match="Mercado Pago recusou"):
            payment_gateway.create_preference(
                title="x", amount=1.0, external_reference="d1", success_url="https://x.example/cb"
            )


class TestGetPayment:
    def test_returns_the_gateway_response(self, monkeypatch):
        fake_sdk = FakeSDK(payment_response={"id": "pay-1", "status": "approved"})
        monkeypatch.setattr(payment_gateway, "_sdk", fake_sdk)

        result = payment_gateway.get_payment("pay-1")

        assert result == {"id": "pay-1", "status": "approved"}
        assert fake_sdk._payment_client.last_call == "pay-1"
