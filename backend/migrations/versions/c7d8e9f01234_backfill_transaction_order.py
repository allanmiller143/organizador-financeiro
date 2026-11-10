"""backfill legacy transaction order

Revision ID: c7d8e9f01234
Revises: b5c6d7e8f901
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa


revision = "c7d8e9f01234"
down_revision = "b5c6d7e8f901"
branch_labels = None
depends_on = None


def upgrade():
    # Linhas antigas não tinham sort_order. Mantemos a ordem que o histórico
    # antigo apresentava (UUID descendente) apenas como desempate inicial; a
    # partir daí novos lançamentos entram no fim e o usuário pode rearranjar.
    op.execute(
        sa.text(
            """
            WITH legacy AS (
                SELECT
                    id,
                    account_id,
                    occurred_on,
                    COALESCE(
                        (
                            SELECT MAX(existing.sort_order)
                            FROM transactions AS existing
                            WHERE existing.account_id = transactions.account_id
                              AND existing.occurred_on = transactions.occurred_on
                              AND existing.sort_order IS NOT NULL
                        ),
                        -1
                    ) AS base_order,
                    ROW_NUMBER() OVER (
                        PARTITION BY account_id, occurred_on
                        ORDER BY id DESC
                    ) - 1 AS legacy_position
                FROM transactions
                WHERE sort_order IS NULL
            )
            UPDATE transactions AS t
            SET sort_order = legacy.base_order + legacy.legacy_position + 1
            FROM legacy
            WHERE t.id = legacy.id
            """
        )
    )


def downgrade():
    # A ordem é um dado operacional; não é seguro apagar os índices existentes.
    pass
