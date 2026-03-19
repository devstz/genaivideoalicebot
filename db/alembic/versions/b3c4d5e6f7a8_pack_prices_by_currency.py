"""pack prices_by_currency JSONB

Revision ID: b3c4d5e6f7a8
Revises: a12b34c56d78
Create Date: 2026-03-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a12b34c56d78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("packs", sa.Column("prices_by_currency", JSONB(astext_type=sa.Text()), nullable=True))
    op.execute(sa.text(
        "UPDATE packs SET prices_by_currency = jsonb_build_object('RUB', to_jsonb(price::numeric)) "
        "WHERE prices_by_currency IS NULL"
    ))


def downgrade() -> None:
    op.drop_column("packs", "prices_by_currency")
