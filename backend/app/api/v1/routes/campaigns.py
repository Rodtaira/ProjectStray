import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.schemas.donation import DonationCheckout, DonationCreate, DonationRead
from app.services import animals as animals_service
from app.services import campaigns as campaigns_service
from app.services import donations as donations_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignRead:
    if data.animal_id is not None:
        animal = await animals_service.get_animal_by_id(db, data.animal_id)
        if animal is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal informado não existe")

    campaign = await campaigns_service.create_campaign(db, data, created_by=current_user.id)
    return campaigns_service.to_read_schema(campaign)


@router.get("", response_model=list[CampaignRead])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
) -> list[CampaignRead]:
    campaigns = await campaigns_service.list_campaigns(db)
    return [campaigns_service.to_read_schema(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CampaignRead:
    campaign = await campaigns_service.get_campaign_by_id(db, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada")
    return campaigns_service.to_read_schema(campaign)


@router.patch("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(
    campaign_id: uuid.UUID,
    data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignRead:
    campaign = await campaigns_service.get_campaign_by_id(db, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada")

    is_owner = campaign.created_by == current_user.id
    is_moderator = current_user.role in (UserRole.moderator, UserRole.admin)
    if not is_owner and not is_moderator:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Só quem criou a campanha ou um moderador pode editar"
        )

    updated = await campaigns_service.update_campaign(db, campaign, data)
    return campaigns_service.to_read_schema(updated)


@router.post(
    "/{campaign_id}/donations",
    response_model=DonationCheckout,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation(
    campaign_id: uuid.UUID,
    data: DonationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DonationCheckout:
    campaign = await campaigns_service.get_campaign_by_id(db, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada")

    success_url = f"{settings.public_backend_url}/api/v1/donations/callback"

    donation, checkout_url = await donations_service.create_donation_with_checkout(
        db,
        campaign_id=campaign.id,
        campaign_title=campaign.title,
        amount=data.amount,
        donor_id=current_user.id,
        success_url=success_url,
    )

    return DonationCheckout(
        donation=donations_service.to_read_schema(donation),
        checkout_url=checkout_url,
    )


@router.get("/{campaign_id}/donations", response_model=list[DonationRead])
async def list_donations(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[DonationRead]:
    # Público de propósito — é o extrato de transparência do crowdfunding.
    donations = await donations_service.list_donations(db, campaign_id)
    return [donations_service.to_read_schema(d) for d in donations]