import sqlite3
import os

DATABASE_PATH = 'database/journal.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    if not os.path.exists('database'):
        os.makedirs('database')

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     date TEXT,
                     text TEXT,
                     mood TEXT,
                     productivity REAL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     entry_id INTEGER,
                     task_text TEXT,
                     status TEXT DEFAULT 'pending',
                     completed INTEGER DEFAULT 0,
                     FOREIGN KEY(entry_id) REFERENCES entries(id)
                 )''')
    conn.commit()
    conn.close()
    print("Database initialized.")

def add_entry(date, text, mood, productivity):
    """Adds a new journal entry to the database and returns the new entry's ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO entries (date, text, mood, productivity) VALUES (?, ?, ?, ?)",
              (date, text, mood, productivity))
    entry_id = c.lastrowid
    conn.commit()
    conn.close()
    return entry_id

def add_task(entry_id, task_text):
    """Adds a new task associated with a journal entry."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tasks (entry_id, task_text) VALUES (?, ?)",
              (entry_id, task_text))
    conn.commit()
    conn.close()

def get_all_entries():
    """Retrieves all journal entries from the database."""
    conn = get_db_connection()
    entries = conn.execute("SELECT * FROM entries ORDER BY date DESC").fetchall()
    conn.close()
    return entries

def get_all_tasks():
    """Retrieves all tasks from the database."""
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY entry_id DESC").fetchall()
    conn.close()
    return tasks

def update_task_status(task_id, completed):
    """Updates the completion status of a task."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed = ? WHERE id = ?", (completed, task_id))
    conn.commit()
    conn.close()
