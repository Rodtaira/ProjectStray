from app.models.animal import Animal, AnimalSex, AnimalSpecies, AnimalStatus  # noqa: F401
from app.models.base import Base
from app.models.campaign import Campaign, CampaignStatus  # noqa: F401
from app.models.donation import Donation, DonationStatus  # noqa: F401
from app.models.sighting import Sighting  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401

# Sempre que criar um modelo novo, importe-o aqui também —
# é assim que o Alembic descobre a tabela na hora do --autogenerate.

__all__ = [
    "Base",
    "Sighting",
    "User",
    "UserRole",
    "Animal",
    "AnimalSex",
    "AnimalSpecies",
    "AnimalStatus",
    "Campaign",
    "CampaignStatus",
    "Donation",
    "DonationStatus",
]