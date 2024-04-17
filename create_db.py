import sqlite3

conn = sqlite3.connect('lib/library.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS files
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             filename TEXT NOT NULL,
             title TEXT NOT NULL,
             author TEXT,
             year TEXT,
             edition TEXT,
             tags TEXT)''')

conn.commit()
conn.close()
