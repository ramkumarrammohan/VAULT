"""Add corporate_events table

Revision ID: add_corporate_events
Revises: 3442f5eafc50
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_corporate_events'
down_revision = '3442f5eafc50'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'corporate_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('stock_id', sa.Integer(), sa.ForeignKey('stocks.id'), nullable=False),
        sa.Column('event_type', sa.Enum('SPLIT', 'DEMERGER', 'MERGER', 'AMALGAMATION', 'DIVIDEND', 'NAME_CHANGE', name='corporateeventtype'), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('ratio', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('related_stock_id', sa.Integer(), sa.ForeignKey('stocks.id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_table('corporate_events')
    op.execute("DROP TYPE IF EXISTS corporateeventtype")