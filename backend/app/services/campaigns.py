from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate


async def create_campaign(db: AsyncSession, data: CampaignCreate, created_by) -> Campaign:
    campaign = Campaign(
        title=data.title,
        description=data.description,
        goal_amount=data.goal_amount,
        animal_id=data.animal_id,
        created_by=created_by,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def get_campaign_by_id(db: AsyncSession, campaign_id) -> Campaign | None:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    return result.scalar_one_or_none()


async def list_campaigns(db: AsyncSession, limit: int = 50) -> list[Campaign]:
    result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def update_campaign(db: AsyncSession, campaign: Campaign, data: CampaignUpdate) -> Campaign:
    if data.title is not None:
        campaign.title = data.title
    if data.description is not None:
        campaign.description = data.description
    if data.status is not None:
        campaign.status = CampaignStatus(data.status)
    await db.commit()
    await db.refresh(campaign)
    return campaign


def to_read_schema(campaign: Campaign) -> CampaignRead:
    return CampaignRead(
        id=campaign.id,
        created_by=campaign.created_by,
        animal_id=campaign.animal_id,
        title=campaign.title,
        description=campaign.description,
        goal_amount=campaign.goal_amount,
        status=campaign.status.value,
        created_at=campaign.created_at,
    )