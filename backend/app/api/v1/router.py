from fastapi import APIRouter

from app.api.v1.routes import (
    animals,
    auth,
    campaigns,
    chat,
    feeding_points,
    matches,
    media,
    moderation,
    sightings,
    users,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(animals.router)
api_router.include_router(sightings.router)
api_router.include_router(matches.router)
api_router.include_router(feeding_points.router)
api_router.include_router(campaigns.router)
api_router.include_router(webhooks.router)
api_router.include_router(media.router)
api_router.include_router(moderation.router)
api_router.include_router(chat.router)
api_router.include_router(chat.ws_router)
