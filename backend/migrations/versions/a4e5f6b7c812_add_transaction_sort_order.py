"""add manual transaction order

Revision ID: a4e5f6b7c812
Revises: 9b3d8e2f4a11
Create Date: 2026-11-08

"""
from alembic import op
import sqlalchemy as sa


revision = "a4e5f6b7c812"
down_revision = "9b3d8e2f4a11"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transactions", sa.Column("sort_order", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("transactions", "sort_order")
