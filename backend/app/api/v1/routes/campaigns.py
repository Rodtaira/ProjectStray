from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.post("", dependencies=[Depends(get_current_user)])
async def create_campaign():
    _not_implemented()


@router.get("")
async def list_campaigns():
    _not_implemented()


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    _not_implemented()


@router.post("/{campaign_id}/donations", dependencies=[Depends(get_current_user)])
async def create_donation(campaign_id: str):
    _not_implemented()


@router.get("/{campaign_id}/donations")
async def list_donations(campaign_id: str):
    """Extrato público (ledger) — fica sem autenticação de propósito,
    é a transparência do crowdfunding."""
    _not_implemented()
