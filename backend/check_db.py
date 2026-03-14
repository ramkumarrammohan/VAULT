import sqlite3
import os

os.chdir(os.path.dirname(__file__))

conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

if tables:
    print("Existing tables:")
    for table in tables:
        print(f"  - {table[0]}")
else:
    print("No tables found in database!")

conn.close()
