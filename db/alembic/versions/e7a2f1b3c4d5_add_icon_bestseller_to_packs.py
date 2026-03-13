"""add_icon_bestseller_to_packs

Revision ID: e7a2f1b3c4d5
Revises: d165b429f075
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7a2f1b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'd165b429f075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('packs', sa.Column('icon', sa.String(50), nullable=False, server_default=sa.text("'payments'")))
    op.add_column('packs', sa.Column('is_bestseller', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('packs', 'is_bestseller')
    op.drop_column('packs', 'icon')
