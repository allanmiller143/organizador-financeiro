"""add investment terms to transactions

Revision ID: 8a2c7f1d9b10
Revises: 59d1636c6b42
Create Date: 2026-11-08

"""
from alembic import op
import sqlalchemy as sa


revision = "8a2c7f1d9b10"
down_revision = "59d1636c6b42"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "transactions",
        sa.Column("cdi_percent", sa.Numeric(precision=6, scale=2), nullable=False, server_default="100.00"),
    )
    op.add_column(
        "transactions",
        sa.Column("term_months", sa.Integer(), nullable=False, server_default="24"),
    )
    op.alter_column("transactions", "cdi_percent", server_default=None)
    op.alter_column("transactions", "term_months", server_default=None)


def downgrade():
    op.drop_column("transactions", "term_months")
    op.drop_column("transactions", "cdi_percent")
