"""Initialize database with all tables including demerger support"""
import sqlite3
import os
from datetime import datetime

os.chdir(os.path.dirname(__file__))

print("Creating database with all tables...")


# Use Config class for database configuration
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from config.config import Config

db_url = Config.SQLALCHEMY_DATABASE_URI
print(f"Using database URL: {db_url}")
if db_url.startswith('sqlite:///'):
    db_path = db_url.replace('sqlite:///', '', 1)
elif db_url.startswith('sqlite://'):
    db_path = db_url.replace('sqlite://', '', 1)
else:
    raise ValueError("Only sqlite databases are supported by this script.")

print(f"Database file path: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create accounts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at DATETIME,
    updated_at DATETIME
)
''')

# Create stocks table
cursor.execute('''
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50),
    sector VARCHAR(100),
    current_price FLOAT,
    last_updated DATETIME,
    created_at DATETIME
)
''')

# Create transactions table with demerger fields
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    transaction_date DATETIME NOT NULL,
    fees FLOAT DEFAULT 0,
    notes TEXT,
    created_at DATETIME,
    demerger_source_stock_id INTEGER,
    demerger_ratio FLOAT,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    FOREIGN KEY (demerger_source_stock_id) REFERENCES stocks(id)
)
''')

# Create holdings table (calculated from transactions)
cursor.execute('''
CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    quantity FLOAT NOT NULL,
    average_price FLOAT NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE (account_id, stock_id)
)
''')

# Create alembic_version table for migration tracking
cursor.execute('''
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
)
''')

# Set the version to the latest migration
cursor.execute("INSERT OR REPLACE INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6')")

conn.commit()
conn.close()

print("\n✅ Database initialized successfully!")
print("\nTables created:")
print("  ✓ accounts")
print("  ✓ stocks")  
print("  ✓ transactions (with SPLIT and DEMERGER support)")
print("  ✓ holdings")
print("\nYou can now:")
print("  1. Start the Flask backend: python app.py")
print("  2. Add accounts, stocks, and transactions via the UI")
print("  3. Use new transaction types: BUY, SELL, SPLIT, DEMERGER")
