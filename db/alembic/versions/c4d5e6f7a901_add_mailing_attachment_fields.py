"""add mailing attachment_path and attachment_type

Revision ID: c4d5e6f7a901
Revises: b3c4d5e6f7a8
Create Date: 2026-04-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c4d5e6f7a901"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mailings", sa.Column("attachment_path", sa.String(length=512), nullable=True))
    op.add_column("mailings", sa.Column("attachment_type", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("mailings", "attachment_type")
    op.drop_column("mailings", "attachment_path")
