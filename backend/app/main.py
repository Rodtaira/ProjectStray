import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(title="App de Animais de Rua - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


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
