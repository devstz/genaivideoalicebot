"""add payment provider fields

Revision ID: a12b34c56d78
Revises: 1d3e5f7a9b2c
Create Date: 2026-03-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a12b34c56d78"
down_revision: Union[str, Sequence[str], None] = "1d3e5f7a9b2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))

    op.add_column("packs", sa.Column("lava_offer_id", sa.String(length=64), nullable=True))

    op.add_column("purchases", sa.Column("provider", sa.String(length=20), nullable=True))
    op.add_column("purchases", sa.Column("external_invoice_id", sa.String(length=64), nullable=True))
    op.add_column("purchases", sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column("purchases", sa.Column("currency", sa.String(length=3), nullable=True))
    op.add_column("purchases", sa.Column("buyer_email", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_purchases_external_invoice_id"), "purchases", ["external_invoice_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_purchases_external_invoice_id"), table_name="purchases")
    op.drop_column("purchases", "buyer_email")
    op.drop_column("purchases", "currency")
    op.drop_column("purchases", "amount")
    op.drop_column("purchases", "external_invoice_id")
    op.drop_column("purchases", "provider")

    op.drop_column("packs", "lava_offer_id")

    op.drop_column("users", "email")
