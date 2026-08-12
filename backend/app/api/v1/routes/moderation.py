from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_moderator, get_current_user

router = APIRouter(tags=["moderation"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.post("/flags", dependencies=[Depends(get_current_user)])
async def create_flag():
    """Lembrar do rate limit (Redis) e da constraint de unicidade
    (flagged_by, content_type, content_id) do modelo de dados."""
    _not_implemented()


@router.get("/moderation/queue", dependencies=[Depends(get_current_moderator)])
async def get_moderation_queue():
    """Filtrar pela região do moderador — nunca devolver a fila inteira
    pra qualquer moderador, só a da área dele."""
    _not_implemented()


@router.post("/moderation/actions", dependencies=[Depends(get_current_moderator)])
async def create_moderation_action():
    _not_implemented()


@router.get("/moderation/actions", dependencies=[Depends(get_current_moderator)])
async def list_moderation_actions():
    """Contém dado pessoal sensível (quem denunciou quem) — acesso
    restrito a moderador/admin, nunca a usuário comum."""
    _not_implemented()
