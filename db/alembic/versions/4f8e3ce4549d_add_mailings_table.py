"""add_mailings_table

Revision ID: 4f8e3ce4549d
Revises: baa77c6a8411
Create Date: 2026-03-12 12:47:47.700334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f8e3ce4549d'
down_revision: Union[str, Sequence[str], None] = 'baa77c6a8411'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('mailings',
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('audience_filter', sa.String(length=30), nullable=False, server_default='all'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('recipient_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mailings'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('mailings')
