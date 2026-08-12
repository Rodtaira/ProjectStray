from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.post("/{match_id}/confirm", dependencies=[Depends(get_current_user)])
async def confirm_match(match_id: str):
    """O match nunca é aplicado automaticamente — essa confirmação manual
    é obrigatória (ver fluxo de matching por IA já desenhado)."""
    _not_implemented()


@router.post("/{match_id}/reject", dependencies=[Depends(get_current_user)])
async def reject_match(match_id: str):
    _not_implemented()
