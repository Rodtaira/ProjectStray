import asyncio
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.campaign import Campaign, CampaignStatus
from app.models.donation import Donation, DonationStatus
from app.schemas.donation import DonationRead
from app.services import payment_gateway


async def create_donation_with_checkout(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    campaign_title: str,
    amount,
    donor_id: uuid.UUID | None,
    success_url: str,
) -> tuple[Donation, str]:
    # Cria a doação primeiro (flush, não commit) só pra existir um id —
    # é esse id que vira o external_reference lá no Mercado Pago.
    donation = Donation(
        campaign_id=campaign_id,
        donor_id=donor_id,
        amount=amount,
        payment_reference="pending",
        status=DonationStatus.pending,
    )
    db.add(donation)
    await db.flush()

    try:
        preference = await asyncio.wait_for(
            run_in_threadpool(
                payment_gateway.create_preference,
                title=f"Doação - {campaign_title}",
                amount=float(amount),
                external_reference=str(donation.id),
                success_url=success_url,
            ),
            timeout=15,
        )
    except asyncio.TimeoutError as exc:
        raise RuntimeError(
            "Tempo esgotado ao conectar com o Mercado Pago (mais de 15s sem resposta)"
        ) from exc

    donation.payment_reference = preference["id"]
    await db.commit()
    await db.refresh(donation)

    return donation, preference["init_point"]


async def get_donation_by_id(db: AsyncSession, donation_id) -> Donation | None:
    result = await db.execute(select(Donation).where(Donation.id == donation_id))
    return result.scalar_one_or_none()


async def list_donations(
    db: AsyncSession, campaign_id: uuid.UUID, limit: int = 50
) -> list[Donation]:
    # Só doações CONFIRMADAS no extrato público — uma tentativa de checkout
    # abandonada não deveria aparecer como se fosse uma doação real.
    result = await db.execute(
        select(Donation)
        .where(Donation.campaign_id == campaign_id, Donation.status == DonationStatus.confirmed)
        .order_by(Donation.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def confirm_donation(db: AsyncSession, donation: Donation) -> None:
    donation.status = DonationStatus.confirmed
    await _maybe_mark_campaign_funded(db, donation.campaign_id)
    await db.commit()


async def _maybe_mark_campaign_funded(db: AsyncSession, campaign_id: uuid.UUID) -> None:
    """Soma as doações confirmadas da campanha e, se atingiu ou passou da
    meta, marca status='funded'. Só transiciona a partir de 'active' — não
    reabre uma campanha já concluída/cancelada.

    Trava a linha da campanha (FOR UPDATE) antes de somar: webhook e
    callback podem confirmar doações da mesma campanha quase ao mesmo
    tempo, e sem o lock as duas leriam o total desatualizado e tentariam
    decidir a transição por conta própria. Com o lock, a segunda espera a
    primeira commitar e aí vê o status já 'funded'.

    Não comita — quem chama decide quando (junto com a confirmação da
    doação, numa única transação)."""
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id).with_for_update()
    )
    campaign = campaign_result.scalar_one_or_none()
    if campaign is None or campaign.status != CampaignStatus.active:
        return

    result = await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.campaign_id == campaign_id,
            Donation.status == DonationStatus.confirmed,
        )
    )
    raised = result.scalar_one()

    if raised >= campaign.goal_amount:
        campaign.status = CampaignStatus.funded


def to_read_schema(donation: Donation) -> DonationRead:
    return DonationRead(
        id=donation.id,
        campaign_id=donation.campaign_id,
        donor_id=donation.donor_id,
        amount=donation.amount,
        status=donation.status.value,
        created_at=donation.created_at,
    )