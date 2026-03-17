"""add admin login and password hash to users

Revision ID: f1b2c3d4e5f6
Revises: c9f4a8d2b1e3
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c9f4a8d2b1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("admin_login", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("admin_password_hash", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_admin_login"), "users", ["admin_login"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_admin_login"), table_name="users")
    op.drop_column("users", "admin_password_hash")
    op.drop_column("users", "admin_login")
