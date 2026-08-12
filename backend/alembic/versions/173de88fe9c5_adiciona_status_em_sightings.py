"""adiciona status em sightings

Revision ID: 173de88fe9c5
Revises: ab27e743018d
Create Date: 2026-08-12 15:00:53.310827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '173de88fe9c5'
down_revision: Union[str, None] = 'ab27e743018d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

sighting_status_enum = postgresql.ENUM(
    'open', 'resolved', name='sighting_status', create_type=False
)


def upgrade() -> None:
    sighting_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'sightings',
        sa.Column('status', sighting_status_enum, server_default='open', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('sightings', 'status')
    sighting_status_enum.drop(op.get_bind(), checkfirst=True)
