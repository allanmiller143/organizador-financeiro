"""add manual reinvestment order

Revision ID: b5c6d7e8f901
Revises: a4e5f6b7c812
Create Date: 2026-11-09

"""
from alembic import op
import sqlalchemy as sa


revision = "b5c6d7e8f901"
down_revision = "a4e5f6b7c812"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transactions", sa.Column("reinvestment_order", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("transactions", "reinvestment_order")
