import hashlib
import hmac

from app.api.v1.routes.webhooks import _verify_signature


def _sign(secret: str, data_id: str, ts: str, request_id: str | None = None) -> str:
    manifest = f"id:{data_id.lower()};"
    if request_id:
        manifest += f"request-id:{request_id};"
    manifest += f"ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


class TestVerifySignature:
    def test_accepts_a_correctly_signed_header(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        v1 = _sign("test-secret", "payment-123", "1700000000", request_id="req-abc")
        x_signature = f"ts=1700000000,v1={v1}"

        assert _verify_signature(x_signature, "req-abc", "payment-123") is True

    def test_accepts_a_correctly_signed_header_without_a_request_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        v1 = _sign("test-secret", "payment-123", "1700000000")
        x_signature = f"ts=1700000000,v1={v1}"

        assert _verify_signature(x_signature, None, "payment-123") is True

    def test_rejects_a_tampered_data_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        v1 = _sign("test-secret", "payment-123", "1700000000", request_id="req-abc")
        x_signature = f"ts=1700000000,v1={v1}"

        # Assinatura foi calculada pro payment-123, mas o data.id que
        # realmente chegou é outro — como um atacante tentando reusar uma
        # assinatura válida pra outro pagamento.
        assert _verify_signature(x_signature, "req-abc", "payment-999") is False

    def test_rejects_the_wrong_secret(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        v1 = _sign("wrong-secret", "payment-123", "1700000000", request_id="req-abc")
        x_signature = f"ts=1700000000,v1={v1}"

        assert _verify_signature(x_signature, "req-abc", "payment-123") is False

    def test_rejects_a_missing_signature_header(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        assert _verify_signature(None, "req-abc", "payment-123") is False

    def test_rejects_a_missing_data_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        assert _verify_signature("ts=1700000000,v1=whatever", "req-abc", None) is False

    def test_rejects_everything_when_no_webhook_secret_is_configured(self, monkeypatch):
        monkeypatch.setattr("app.api.v1.routes.webhooks.settings.mp_webhook_secret", "")
        v1 = _sign("", "payment-123", "1700000000", request_id="req-abc")
        x_signature = f"ts=1700000000,v1={v1}"

        assert _verify_signature(x_signature, "req-abc", "payment-123") is False

    def test_rejects_a_header_missing_the_v1_part(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        assert _verify_signature("ts=1700000000", "req-abc", "payment-123") is False

    def test_rejects_a_header_missing_the_ts_part(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )

        assert _verify_signature("v1=deadbeef", "req-abc", "payment-123") is False

    def test_a_signature_computed_with_the_request_id_does_not_verify_without_it(
        self, monkeypatch
    ):
        # Prova que o request-id realmente entra no manifesto assinado: uma
        # assinatura calculada COM ele não deve bater se validarmos SEM ele.
        monkeypatch.setattr(
            "app.api.v1.routes.webhooks.settings.mp_webhook_secret", "test-secret"
        )
        v1 = _sign("test-secret", "payment-123", "1700000000", request_id="req-abc")
        x_signature = f"ts=1700000000,v1={v1}"

        assert _verify_signature(x_signature, None, "payment-123") is False
