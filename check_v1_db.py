import sqlite3
import os

db_path = "../ccs_quotes.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print(f"Database: {db_path}")
print(f"File size: {os.path.getsize(db_path)} bytes")
print(f"Tables found: {len(tables)}")
print(f"Table names: {tables}")

conn.close()




