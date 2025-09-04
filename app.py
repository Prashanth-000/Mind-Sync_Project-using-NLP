from flask import Flask, render_template, request, jsonify
from nlp.analysis import analyze_text
from nlp.task_extractor import extract_tasks
from scorer import custom_productivity_score
import sqlite3
from datetime import datetime
import os
from collections import defaultdict
from flask import redirect, url_for
from database.db import init_db, add_entry, add_task, get_all_entries, get_all_tasks, update_task_status

app = Flask(__name__)

# def init_db():
#     if not os.path.exists('database'):
#         os.makedirs('database')

#     conn = sqlite3.connect('database/journal.db')
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS entries (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     date TEXT,
#                     text TEXT,
#                     mood TEXT,
#                     productivity REAL
#                 )''')
#     c.execute('''CREATE TABLE IF NOT EXISTS tasks (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     entry_id INTEGER,
#                     task_text TEXT,
#                     status TEXT DEFAULT 'pending',
#                     completed INTEGER DEFAULT 0,
#                     FOREIGN KEY(entry_id) REFERENCES entries(id)
#                 )''')
#     conn.commit()
#     conn.close()
@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect('database/journal.db')
    c = conn.cursor()

    # Fetch journal entries
    c.execute("SELECT date, text, mood, productivity FROM entries ORDER BY date ASC")
    raw_entries = c.fetchall()

    # Fetch pending tasks
    c.execute("SELECT id, task_text FROM tasks WHERE status = 'pending' AND completed = 0")
    pending_tasks = c.fetchall()

    # Fetch recent and completed tasks
    c.execute("SELECT task_text, date(entries.date) FROM tasks JOIN entries ON tasks.entry_id = entries.id ORDER BY tasks.id DESC LIMIT 5")
    recent_tasks = c.fetchall()

    c.execute("SELECT task_text, date(entries.date) FROM tasks JOIN entries ON tasks.entry_id = entries.id WHERE tasks.completed = 1 ORDER BY tasks.id DESC LIMIT 5")
    completed_tasks = c.fetchall()

    # Fetch chart data for mood/productivity
    c.execute('''SELECT date, 
                        AVG(productivity), 
                        AVG(CASE mood 
                            WHEN 'positive' THEN 1 
                            WHEN 'neutral' THEN 0 
                            WHEN 'negative' THEN -1 
                            ELSE 0 END)
                 FROM entries 
                 GROUP BY date 
                 ORDER BY date DESC 
                 LIMIT 30''')
    chart_data = c.fetchall()

    # Now, no need to close here. We'll do it after gathering all data.
    grouped = defaultdict(list)
    for entry in raw_entries:
        grouped[entry[0]].append(entry)

    entries_by_day = []
    mood_score_map = {"negative": -1, "neutral": 0, "positive": 1}

    # Fetch tasks for each journal entry
    for date, items in grouped.items():
        moods = [e[2] for e in items]
        prod_scores = [e[3] for e in items]
        mood_numeric = [mood_score_map.get(m, 0) for m in moods]

        avg_mood_score = sum(mood_numeric) / len(mood_numeric)
        avg_prod_score = sum(prod_scores) / len(prod_scores)

        numbered_entries = list(enumerate(items, start=1))

        # Fetch tasks for each entry on the day
        tasks_for_day = []
        for entry in items:
            entry_id = entry[0]  # Assuming entry ID is the first element
            c.execute("SELECT task_text FROM tasks WHERE entry_id = ?", (entry_id,))
            tasks = c.fetchall()
            tasks_for_day.append({
                "entry_id": entry_id,
                "tasks": [task[0] for task in tasks]  # List of tasks for this entry
            })

        entries_by_day.append({
            "date": date,
            "avg_mood_score": round(avg_mood_score, 2),
            "avg_productivity": round(avg_prod_score, 2),
            "entries": numbered_entries,
            "tasks_for_day": tasks_for_day  # Add tasks for each entry
        })

    entries_by_day.sort(key=lambda x: x["date"])

    weekly_mood = {}
    for week, items in grouped.items():
        moods = [e[2] for e in items]
        mood_numeric = [mood_score_map.get(m, 0) for m in moods]
        weekly_mood[week] = round(sum(mood_numeric) / len(mood_numeric), 2)

    conn.close()  # Close the connection after all database queries are completed.

    return render_template("index.html",
                           entries_by_day=entries_by_day,
                           pending_tasks=pending_tasks,
                           recent_tasks=recent_tasks,
                           completed_tasks=completed_tasks,
                           chart_data=chart_data,
                           weekly_mood=weekly_mood)

@app.route("/submit_journal_ajax", methods=["POST"])
def submit_journal_ajax():
    data = request.get_json()
    text = data["journal"]
    analysis = analyze_text(text)

    # Use your custom productivity calculation here
    prod_score = custom_productivity_score(text)

    conn = sqlite3.connect('database/journal.db')
    c = conn.cursor()
    c.execute("INSERT INTO entries (date, text, mood, productivity) VALUES (?, ?, ?, ?)",
              (datetime.now().date(), text, analysis['mood'], prod_score))
    entry_id = c.lastrowid

    tasks = extract_tasks(text)
    for task in tasks:
        c.execute("INSERT INTO tasks (entry_id, task_text) VALUES (?, ?)", (entry_id, task))
    conn.commit()
    conn.close()

    return jsonify({
        "mood": analysis['mood'],
        "productivity": prod_score,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "tasks": tasks
    })

@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    conn = sqlite3.connect('database/journal.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route("/api/chart_data/<period>")
def chart_data(period):
    conn = sqlite3.connect('database/journal.db')
    c = conn.cursor()

    if period == "daily":
        query = '''
            SELECT date, 
                   AVG(productivity), 
                   AVG(CASE mood 
                       WHEN 'positive' THEN 1 
                       WHEN 'neutral' THEN 0 
                       WHEN 'negative' THEN -1 
                       ELSE 0 END)
            FROM entries 
            GROUP BY date 
            ORDER BY date DESC 
            LIMIT 30
        '''
    elif period == "weekly":
        query = '''
            SELECT strftime('%Y-W%W', date), 
                   AVG(productivity), 
                   AVG(CASE mood 
                       WHEN 'positive' THEN 1 
                       WHEN 'neutral' THEN 0 
                       WHEN 'negative' THEN -1 
                       ELSE 0 END)
            FROM entries 
            GROUP BY strftime('%Y-W%W', date) 
            ORDER BY date DESC 
            LIMIT 12
        '''
    elif period == "monthly":
        query = '''
            SELECT strftime('%Y-%m', date), 
                   AVG(productivity), 
                   AVG(CASE mood 
                       WHEN 'positive' THEN 1 
                       WHEN 'neutral' THEN 0 
                       WHEN 'negative' THEN -1 
                       ELSE 0 END)
            FROM entries 
            GROUP BY strftime('%Y-%m', date) 
            ORDER BY date DESC 
            LIMIT 12
        '''
    else:
        return jsonify({"error": "Invalid period"}), 400

    c.execute(query)
    results = c.fetchall()
    conn.close()

    return jsonify([{
        "label": row[0],
        "productivity": round(row[1], 2) if row[1] else 0,
        "mood": round(row[2], 2) if row[2] else 0
    } for row in results])

@app.route('/day_view/<date>')
def day_view(date):
    conn = sqlite3.connect('database/journal.db')
    cursor = conn.cursor()

    # Get all entries for the date
    cursor.execute("SELECT id, text, mood, productivity FROM entries WHERE date = ?", (date,))
    rows = cursor.fetchall()

    entries = []
    for row in rows:
        entry_id, journal_text, mood, productivity = row

        # Get tasks for this entry
        cursor.execute("SELECT task_text, status, completed FROM tasks WHERE entry_id = ?", (entry_id,))
        tasks = cursor.fetchall()

        entries.append({
            'journal_text': journal_text,
            'mood': mood,
            'productivity': productivity,
            'tasks': tasks
        })

    conn.close()

    return render_template('day_view.html', date=date, entries=entries)

    from flask import request, redirect, url_for, flash
from flask import request, redirect, url_for

@app.route('/delete_entries', methods=['POST'])
def delete_entries():
    # Get list of selected entry IDs from form (can be empty)
    entry_ids = request.form.getlist('entry_ids')
    date = request.form.get('date')  # date passed in hidden input
    
    if entry_ids:
        conn = sqlite3.connect('database/journal.db')
        cursor = conn.cursor()
        
        # Use a parameterized query with placeholders for safety
        query = f"DELETE FROM entries WHERE id IN ({','.join(['?']*len(entry_ids))})"
        cursor.execute(query, entry_ids)
        
        # Also delete associated tasks for deleted entries
        query_tasks = f"DELETE FROM tasks WHERE entry_id IN ({','.join(['?']*len(entry_ids))})"
        cursor.execute(query_tasks, entry_ids)
        
        conn.commit()
        conn.close()

    # Redirect back to the day view page of the same date
    return redirect(url_for('day_view', date=date))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
