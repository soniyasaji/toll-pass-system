import sqlite3

conn = sqlite3.connect('tollpass.db')
c = conn.cursor()
c.execute("UPDATE users SET remaining_crossings = 5 WHERE user_id = '1'")
conn.commit()
conn.close()
print("✅ Added 5 crossings to User 1")