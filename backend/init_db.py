"""Initialize database by applying all Alembic migrations."""
import os
import sys

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask_migrate import upgrade
from app import create_app

def init_db():
    app = create_app()
    with app.app_context():
        print(f"Applying migrations to: {app.config['SQLALCHEMY_DATABASE_URI']}")
        upgrade()
        print("Database initialised successfully.")

if __name__ == '__main__':
    init_db()

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
