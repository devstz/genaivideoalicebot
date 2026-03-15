"""add media_folder to generations

Revision ID: c9f4a8d2b1e3
Revises: 7f8a9b0c1d2e
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9f4a8d2b1e3"
down_revision: Union[str, Sequence[str], None] = "7f8a9b0c1d2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generations", sa.Column("media_folder", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("generations", "media_folder")
