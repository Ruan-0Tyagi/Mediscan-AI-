import sqlite3

conn = sqlite3.connect("users.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    approved INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

print("Database and users table created successfully.")
