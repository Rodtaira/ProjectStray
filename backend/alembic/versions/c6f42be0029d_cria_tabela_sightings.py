"""cria tabela sightings

Revision ID: c6f42be0029d
Revises: 
Create Date: 2026-08-11 18:33:35.818200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2.types
import pgvector.sqlalchemy.vector

revision: str = 'c6f42be0029d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('sightings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeogFromText', name='geography', nullable=False, spatial_index=False), nullable=False),
    sa.Column('photo_embedding', pgvector.sqlalchemy.vector.VECTOR(dim=512), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sightings_location', 'sightings', ['location'], unique=False, postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('idx_sightings_location', table_name='sightings', postgresql_using='gist')
    op.drop_table('sightings')
