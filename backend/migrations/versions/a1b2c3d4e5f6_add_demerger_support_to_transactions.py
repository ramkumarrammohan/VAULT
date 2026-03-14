"""Add demerger support to transactions

Revision ID: a1b2c3d4e5f6
Revises: 5d77eb6e3225
Create Date: 2026-01-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '5d77eb6e3225'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to transactions table
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('demerger_source_stock_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('demerger_ratio', sa.Float(), nullable=True))
        batch_op.create_foreign_key('fk_demerger_source_stock', 'stocks', ['demerger_source_stock_id'], ['id'])


def downgrade():
    # Remove columns from transactions table
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_demerger_source_stock', type_='foreignkey')
        batch_op.drop_column('demerger_ratio')
        batch_op.drop_column('demerger_source_stock_id')
