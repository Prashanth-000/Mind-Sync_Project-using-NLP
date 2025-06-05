import sqlite3
conn = sqlite3.connect('database/journal.db')
c = conn.cursor()
c.execute("PRAGMA table_info(tasks)")
print(c.fetchall())
conn.close()
