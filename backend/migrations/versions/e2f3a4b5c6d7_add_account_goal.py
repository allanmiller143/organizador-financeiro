"""add optional account balance goal

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accounts", sa.Column("goal_amount", sa.Numeric(14, 2), nullable=True))


def downgrade():
    op.drop_column("accounts", "goal_amount")
