import logging
import uuid

import redis.asyncio as redis
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.donation import DonationStatus
from app.services import donations as donations_service
from app.services import payment_gateway

logger = logging.getLogger("donation_callback")

app = FastAPI(title="App de Animais de Rua - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/donations/callback", response_class=HTMLResponse)
async def donation_callback(
    payment_id: str | None = None,
    external_reference: str | None = None,
    db=Depends(get_db),
):
    """Confirma a doação a partir do retorno do checkout — caminho
    independente do webhook, que se mostrou pouco confiável em notificações
    de pagamento real neste ambiente de teste (ver DOCUMENTACAO.md §7.3/7.4).

    Nunca confia nos parâmetros da URL sozinhos: sempre reverifica o
    pagamento pela API autenticada do Mercado Pago antes de confirmar.
    """
    confirmed = False

    if payment_id and external_reference:
        try:
            donation_id = uuid.UUID(external_reference)
        except ValueError:
            logger.warning("external_reference não é um UUID válido: %r", external_reference)
            donation_id = None

        if donation_id is not None:
            try:
                payment = await run_in_threadpool(payment_gateway.get_payment, payment_id)
            except Exception:
                logger.exception("Erro ao buscar payment_id=%s no Mercado Pago", payment_id)
                payment = {}

            logger.warning(
                "Callback: payment_id=%s status=%s donation_id=%s",
                payment_id, payment.get("status"), donation_id,
            )

            if payment.get("status") == "approved":
                donation = await donations_service.get_donation_by_id(db, donation_id)
                if donation is None:
                    logger.warning("Doação %s não encontrada no banco", donation_id)
                elif donation.status != DonationStatus.confirmed:
                    await donations_service.confirm_donation(db, donation)
                    logger.warning("Doação %s confirmada via callback", donation_id)
                confirmed = True

    message = (
        "Pagamento confirmado! Pode fechar esta aba e voltar pro app."
        if confirmed
        else "Pagamento processado. Pode fechar esta aba e voltar pro app."
    )
    return f"<html><body><h1>{message}</h1></body></html>"


@app.get("/health")
async def health_check():
    """Verifica se banco (com PostGIS e pgvector) e Redis estão respondendo.
    Use isso pra confirmar que o ambiente local está de pé corretamente.
    """
    status = {"database": "erro", "postgis": "erro", "pgvector": "erro", "redis": "erro"}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            status["database"] = "ok"

            postgis_version = await conn.execute(text("SELECT PostGIS_Version()"))
            status["postgis"] = postgis_version.scalar()

            has_pgvector = await conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            status["pgvector"] = "ok" if has_pgvector.scalar() else "extensão não encontrada"
    except Exception as exc:
        status["database"] = f"erro: {exc}"

    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        status["redis"] = "ok"
        await redis_client.close()
    except Exception as exc:
        status["redis"] = f"erro: {exc}"

    return status