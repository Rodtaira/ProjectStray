import hashlib
import hmac
import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db
from app.core.config import settings
from app.models.donation import DonationStatus
from app.services import donations as donations_service
from app.services import payment_gateway

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("webhook_debug")


def _verify_signature(
    x_signature: str | None, x_request_id: str | None, data_id: str | None
) -> bool:
    """Implementa a validação de assinatura HMAC do Mercado Pago.

    Formato do header x-signature: "ts=<timestamp>,v1=<hash>"
    Manifesto assinado: "id:<data.id em minúsculo>;request-id:<x-request-id>;ts:<ts>;"
    """
    if not x_signature or not data_id or not settings.mp_webhook_secret:
        logger.warning(
            "Webhook rejeitado por dado faltando: x_signature=%s data_id=%s secret_ok=%s",
            bool(x_signature), data_id, bool(settings.mp_webhook_secret),
        )
        return False

    parts = dict(item.strip().split("=", 1) for item in x_signature.split(",") if "=" in item)
    ts = parts.get("ts")
    v1 = parts.get("v1")
    if not ts or not v1:
        logger.warning("Webhook rejeitado: x-signature sem ts/v1. Header cru: %r", x_signature)
        return False

    manifest = f"id:{data_id.lower()};"
    if x_request_id:
        manifest += f"request-id:{x_request_id};"
    manifest += f"ts:{ts};"

    expected = hmac.new(
        settings.mp_webhook_secret.encode(), manifest.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, v1):
        logger.warning(
            "Assinatura não bateu. manifest=%r esperado=%s recebido=%s",
            manifest, expected, v1,
        )
        return False

    return True


@router.post("/payments/mercadopago")
async def mercadopago_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    data_id = request.query_params.get("data.id") or request.query_params.get("id")

    if not _verify_signature(x_signature, x_request_id, data_id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Assinatura inválida")

    body = await request.json()
    if body.get("type") != "payment":
        return {"ok": True}

    payment_id = body.get("data", {}).get("id") or data_id
    payment = await run_in_threadpool(payment_gateway.get_payment, payment_id)

    external_reference = payment.get("external_reference")
    if payment.get("status") == "approved" and external_reference:
        try:
            donation_id = uuid.UUID(external_reference)
        except ValueError:
            donation_id = None

        if donation_id is not None:
            donation = await donations_service.get_donation_by_id(db, donation_id)
            if donation is not None and donation.status != DonationStatus.confirmed:
                await donations_service.confirm_donation(db, donation)

    return {"ok": True}
