import sqlite3

conn = sqlite3.connect("users.db")
rows = conn.execute("SELECT id, email, approved FROM users").fetchall()
conn.close()

for r in rows:
    print(r)
