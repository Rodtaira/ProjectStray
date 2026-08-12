import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.donation import Donation, DonationStatus
from app.schemas.donation import DonationRead
from app.services import payment_gateway


async def create_donation_with_checkout(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    campaign_title: str,
    amount,
    donor_id: uuid.UUID | None,
    notification_url: str,
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
                notification_url=notification_url,
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


async def list_donations(db: AsyncSession, campaign_id: uuid.UUID) -> list[Donation]:
    # Só doações CONFIRMADAS no extrato público — uma tentativa de checkout
    # abandonada não deveria aparecer como se fosse uma doação real.
    result = await db.execute(
        select(Donation)
        .where(Donation.campaign_id == campaign_id, Donation.status == DonationStatus.confirmed)
        .order_by(Donation.created_at.desc())
    )
    return list(result.scalars().all())


async def confirm_donation(db: AsyncSession, donation: Donation) -> None:
    donation.status = DonationStatus.confirmed
    await db.commit()


def to_read_schema(donation: Donation) -> DonationRead:
    return DonationRead(
        id=donation.id,
        campaign_id=donation.campaign_id,
        donor_id=donation.donor_id,
        amount=donation.amount,
        status=donation.status.value,
        created_at=donation.created_at,
    )