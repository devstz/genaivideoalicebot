"""add utm campaigns clicks registrations

Revision ID: 2b4c6d8e9f01
Revises: 1d3e5f7a9b2c
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2b4c6d8e9f01"
down_revision: Union[str, Sequence[str], None] = "1d3e5f7a9b2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "utm_campaigns",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("start_code", sa.String(length=120), nullable=False),
        sa.Column("utm_source", sa.String(length=120), nullable=True),
        sa.Column("utm_medium", sa.String(length=120), nullable=True),
        sa.Column("utm_campaign", sa.String(length=120), nullable=True),
        sa.Column("utm_content", sa.String(length=120), nullable=True),
        sa.Column("utm_term", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utm_campaigns")),
    )
    op.create_index(op.f("ix_utm_campaigns_start_code"), "utm_campaigns", ["start_code"], unique=True)
    op.create_index(op.f("ix_utm_campaigns_is_active"), "utm_campaigns", ["is_active"], unique=False)

    op.create_table(
        "utm_clicks",
        sa.Column("utm_campaign_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["utm_campaign_id"], ["utm_campaigns.id"], name=op.f("fk_utm_clicks_utm_campaign_id_utm_campaigns"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name=op.f("fk_utm_clicks_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utm_clicks")),
        sa.UniqueConstraint("utm_campaign_id", "user_id", name="uq_utm_clicks_utm_campaign_user"),
    )
    op.create_index(op.f("ix_utm_clicks_utm_campaign_id"), "utm_clicks", ["utm_campaign_id"], unique=False)
    op.create_index(op.f("ix_utm_clicks_user_id"), "utm_clicks", ["user_id"], unique=False)

    op.create_table(
        "utm_registrations",
        sa.Column("utm_campaign_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["utm_campaign_id"], ["utm_campaigns.id"], name=op.f("fk_utm_registrations_utm_campaign_id_utm_campaigns"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name=op.f("fk_utm_registrations_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utm_registrations")),
        sa.UniqueConstraint("utm_campaign_id", "user_id", name="uq_utm_regs_utm_campaign_user"),
    )
    op.create_index(op.f("ix_utm_registrations_utm_campaign_id"), "utm_registrations", ["utm_campaign_id"], unique=False)
    op.create_index(op.f("ix_utm_registrations_user_id"), "utm_registrations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_utm_registrations_user_id"), table_name="utm_registrations")
    op.drop_index(op.f("ix_utm_registrations_utm_campaign_id"), table_name="utm_registrations")
    op.drop_table("utm_registrations")

    op.drop_index(op.f("ix_utm_clicks_user_id"), table_name="utm_clicks")
    op.drop_index(op.f("ix_utm_clicks_utm_campaign_id"), table_name="utm_clicks")
    op.drop_table("utm_clicks")

    op.drop_index(op.f("ix_utm_campaigns_is_active"), table_name="utm_campaigns")
    op.drop_index(op.f("ix_utm_campaigns_start_code"), table_name="utm_campaigns")
    op.drop_table("utm_campaigns")
