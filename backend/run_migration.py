"""Simple migration runner"""
import sqlite3
import os

# Change to backend directory
os.chdir(os.path.dirname(__file__))

# Check if database exists in instance folder
db_path = 'instance/portfolio.db'
if not os.path.exists(db_path):
    print(f"❌ Database file '{db_path}' not found!")
    print("\nPlease make sure your database exists at backend/instance/portfolio.db")
    exit(1)

# Run the migration directly using SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if transactions table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
if not cursor.fetchone():
    print("❌ Transactions table does not exist!")
    print("\nPlease initialize the database first")
    conn.close()
    exit(1)

print("📊 Current database schema:")
cursor.execute("PRAGMA table_info(transactions)")
columns = cursor.fetchall()
existing_cols = [col[1] for col in columns]
print(f"  Existing columns: {', '.join(existing_cols)}")

# Add new columns
print("\n🔨 Adding demerger support columns...")

try:
    cursor.execute('ALTER TABLE transactions ADD COLUMN demerger_source_stock_id INTEGER')
    print("✅ Added demerger_source_stock_id column")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("✅ Column demerger_source_stock_id already exists")
    else:
        print(f"❌ Error adding demerger_source_stock_id: {e}")
        conn.close()
        exit(1)

try:
    cursor.execute('ALTER TABLE transactions ADD COLUMN demerger_ratio REAL')
    print("✅ Added demerger_ratio column")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("✅ Column demerger_ratio already exists")
    else:
        print(f"❌ Error adding demerger_ratio: {e}")
        conn.close()
        exit(1)

conn.commit()

# Verify the changes
print("\n📊 Updated database schema:")
cursor.execute("PRAGMA table_info(transactions)")
columns = cursor.fetchall()
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()

print("\n✅ Migration completed successfully!")
print("\n🎉 Your existing data is preserved!")
print("\nYou can now use:")
print("• SPLIT - For stock splits/bonus shares (set price=0)")
print("• DEMERGER - For corporate demergers")
print("  └─ Specify source stock and ratio (e.g., 1:1 = 1.0, 1:0.5 = 0.5)")
print("\n⚠️  Important: Restart your Flask backend to reload the model changes!")
