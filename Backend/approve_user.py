import sqlite3

email = "deaftyagi23@gmail.com"   # change this to the real user email

conn = sqlite3.connect("users.db")
conn.execute("UPDATE users SET approved=1 WHERE email=?", (email,))
conn.commit()
conn.close()

print("User approved successfully!")
