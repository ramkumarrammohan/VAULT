"""Add cost allocation fields to corporate_events

Revision ID: add_cost_pct_to_corporate_events
Revises: add_corporate_events
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_cost_pct_to_corporate_events'
down_revision = 'add_corporate_events'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('corporate_events', sa.Column('parent_cost_pct', sa.Float(), nullable=True))
    op.add_column('corporate_events', sa.Column('demerged_cost_pct', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('corporate_events', 'parent_cost_pct')
    op.drop_column('corporate_events', 'demerged_cost_pct')
