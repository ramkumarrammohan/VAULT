"""Replace holding_id with broker_id in transactions

Revision ID: 962028d53421
Revises: 7a178d80c2ab
Create Date: 2025-12-14 21:56:48.421327

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '962028d53421'
down_revision = '7a178d80c2ab'
branch_labels = None
depends_on = None


def upgrade():
    # Since we're changing the schema significantly and SQLite doesn't support
    # complex alterations, we'll recreate the table
    
    # Step 1: Create new transactions table with correct schema
    op.create_table('transactions_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('broker_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('fees', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['broker_id'], ['brokers.id'], ),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 2: Migrate data - copy transactions with broker_id from holdings
    op.execute('''
        INSERT INTO transactions_new (id, broker_id, stock_id, transaction_type, quantity, price, transaction_date, fees, notes, created_at)
        SELECT t.id, h.broker_id, t.stock_id, t.transaction_type, t.quantity, t.price, t.transaction_date, t.fees, t.notes, t.created_at
        FROM transactions t
        JOIN holdings h ON t.holding_id = h.id
    ''')
    
    # Step 3: Drop old table and rename new one
    op.drop_table('transactions')
    op.rename_table('transactions_new', 'transactions')


def downgrade():
    # Recreate old table structure
    op.create_table('transactions_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('holding_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('fees', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['holding_id'], ['holdings.id'], ),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Note: This downgrade will lose broker_id -> holding_id mapping
    # In a production environment, you'd need a more sophisticated approach
    op.execute('''
        INSERT INTO transactions_old (id, holding_id, stock_id, transaction_type, quantity, price, transaction_date, fees, notes, created_at)
        SELECT t.id, 
               (SELECT h.id FROM holdings h WHERE h.broker_id = t.broker_id AND h.stock_id = t.stock_id LIMIT 1) as holding_id,
               t.stock_id, t.transaction_type, t.quantity, t.price, t.transaction_date, t.fees, t.notes, t.created_at
        FROM transactions t
    ''')
    
    op.drop_table('transactions')
    op.rename_table('transactions_old', 'transactions')
