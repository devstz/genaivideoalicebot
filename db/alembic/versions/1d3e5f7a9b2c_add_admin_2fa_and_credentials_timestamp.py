"""add admin 2fa flag and credentials timestamp

Revision ID: 1d3e5f7a9b2c
Revises: f1b2c3d4e5f6
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1d3e5f7a9b2c"
down_revision: Union[str, Sequence[str], None] = "f1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "admin_require_telegram_2fa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("admin_credentials_set_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_admin_login ON users (admin_login)"
    )


def downgrade() -> None:
    op.drop_column("users", "admin_credentials_set_at")
    op.drop_column("users", "admin_require_telegram_2fa")
