"""Rename brokers to accounts

Revision ID: 5d77eb6e3225
Revises: 962028d53421
Create Date: 2025-12-14 22:39:28.784179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d77eb6e3225'
down_revision = '962028d53421'
branch_labels = None
depends_on = None


def upgrade():
    # Rename brokers table to accounts
    op.rename_table('brokers', 'accounts')
    
    # Update holdings table
    with op.batch_alter_table('holdings', schema=None) as batch_op:
        batch_op.alter_column('broker_id', new_column_name='account_id')
        batch_op.drop_constraint('unique_broker_stock', type_='unique')
        batch_op.create_unique_constraint('unique_account_stock', ['account_id', 'stock_id'])
    
    # Update transactions table  
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('broker_id', new_column_name='account_id')


def downgrade():
    # Reverse: Update transactions table
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('account_id', new_column_name='broker_id')
    
    # Reverse: Update holdings table
    with op.batch_alter_table('holdings', schema=None) as batch_op:
        batch_op.drop_constraint('unique_account_stock', type_='unique')
        batch_op.create_unique_constraint('unique_broker_stock', ['broker_id', 'stock_id'])
        batch_op.alter_column('account_id', new_column_name='broker_id')
    
    # Reverse: Rename accounts table back to brokers
    op.rename_table('accounts', 'brokers')
