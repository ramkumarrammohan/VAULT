"""add currency to stocks

Revision ID: a1b2c3d4e5f6
Revises: 30bfabbcb919
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '14f9da4ed6c9'
branch_labels = None
depends_on = None


def upgrade():
    # Add currency column (nullable so existing rows are unaffected initially)
    op.add_column('stocks', sa.Column('currency', sa.String(3), nullable=True))

    # Backfill: derive currency from exchange field
    op.execute("""
        UPDATE stocks
        SET currency = CASE
            WHEN exchange IN ('NSE', 'BSE') THEN 'INR'
            WHEN symbol LIKE '%.NS' OR symbol LIKE '%.BO' THEN 'INR'
            WHEN exchange IN ('NYSE', 'NASDAQ', 'NMS', 'NYQ', 'NGM', 'NCM', 'ASE') THEN 'USD'
            ELSE NULL
        END
    """)


def downgrade():
    op.drop_column('stocks', 'currency')
