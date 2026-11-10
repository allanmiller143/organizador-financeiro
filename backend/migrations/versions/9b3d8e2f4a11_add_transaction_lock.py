"""add transaction lock flag

Revision ID: 9b3d8e2f4a11
Revises: 8a2c7f1d9b10
Create Date: 2026-11-08

"""
from alembic import op
import sqlalchemy as sa


revision = "9b3d8e2f4a11"
down_revision = "8a2c7f1d9b10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "transactions",
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("transactions", "locked", server_default=None)
    op.execute(
        "UPDATE transactions SET locked = TRUE "
        "WHERE kind = 'DEPOSIT' AND cdi_percent > 100"
    )


def downgrade():
    op.drop_column("transactions", "locked")
