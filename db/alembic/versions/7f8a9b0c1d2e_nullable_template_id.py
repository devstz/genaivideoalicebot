"""nullable template_id in generations

Revision ID: 7f8a9b0c1d2e
Revises: 56d7950d4277
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7f8a9b0c1d2e'
down_revision: Union[str, Sequence[str], None] = '56d7950d4277'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'generations',
        'template_id',
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'generations',
        'template_id',
        existing_type=sa.Integer(),
        nullable=False,
    )
