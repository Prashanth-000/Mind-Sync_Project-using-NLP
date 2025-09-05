from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from collections import defaultdict
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# --- Import the real NLP functions from their dedicated files ---
from nlp.analysis import analyze_text
from nlp.task_extractor import extract_tasks
from nlp.scorer import custom_productivity_score

# --- Import your database functions and the User model ---
from database.db import (
    init_db, add_entry, add_task, update_task_status,
    get_all_entries_sorted_asc, get_pending_tasks, 
    get_tasks_with_entry_info, get_chart_data, get_tasks_for_entry_ids,
    execute_aggregation, get_entries_and_tasks_for_date,
    delete_entries_and_tasks
)
from models import User

app = Flask(__name__)
# IMPORTANT: You must set a secret key for session management to work.
app.config['SECRET_KEY'] = 'a_very_secret_and_long_random_string_for_security'

# --- Initialize Extensions ---
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to load the current user from the database."""
    return User.find_by_id(user_id)
login_manager.login_view = 'login' # Redirect to 'login' view if user is not authenticated
login_manager.login_message_category = 'info'

init_db() # Initialize the database connection

# --- NEW: Authentication Routes ---
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.find_by_email(request.form.get('email'))
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        if User.find_by_email(email):
            flash('That email is already registered.', 'warning')
            return redirect(url_for('register'))
        
        User.create(email, request.form.get('password'))
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- UPDATED: All Routes Below are Now Protected and User-Specific ---

@app.route("/")
@login_required
def index():
    user_id = current_user.get_id()
    raw_entries = get_all_entries_sorted_asc(user_id)
    pending_tasks = get_pending_tasks(user_id)
    recent_tasks = get_tasks_with_entry_info(user_id, completed_status=None, limit=5)
    completed_tasks = get_tasks_with_entry_info(user_id, completed_status=True, limit=5)
    chart_data = get_chart_data(user_id, limit=30)
    
    grouped = defaultdict(list)
    for entry in raw_entries:
        grouped[entry['date']].append(entry)

    entries_by_day = []
    mood_score_map = {"negative": -1, "neutral": 0, "positive": 1}
    all_entry_ids = [entry['_id'] for entry in raw_entries]
    all_tasks = get_tasks_for_entry_ids(user_id, all_entry_ids)
    
    tasks_by_entry_id = defaultdict(list)
    for task in all_tasks:
        tasks_by_entry_id[task['entry_id']].append(task['task_text'])

    for date, items in grouped.items():
        moods = [e['mood'] for e in items]
        prod_scores = [e['productivity'] for e in items]
        mood_numeric = [mood_score_map.get(m, 0) for m in moods]
        avg_mood_score = sum(mood_numeric) / len(mood_numeric) if mood_numeric else 0
        avg_prod_score = sum(prod_scores) / len(prod_scores) if prod_scores else 0
        numbered_entries = list(enumerate(items, start=1))
        tasks_for_day = [{"entry_id": entry['_id'], "tasks": tasks_by_entry_id.get(entry['_id'], [])} for entry in items]
        entries_by_day.append({
            "date": date, "avg_mood_score": round(avg_mood_score, 2),
            "avg_productivity": round(avg_prod_score, 2), "entries": numbered_entries,
            "tasks_for_day": tasks_for_day
        })
    entries_by_day.sort(key=lambda x: x["date"], reverse=True)

    weekly_mood = {} # This logic might need refinement for weekly grouping
    for date, items in grouped.items():
        moods = [e['mood'] for e in items]
        mood_numeric = [mood_score_map.get(m, 0) for m in moods]
        if mood_numeric: weekly_mood[date] = round(sum(mood_numeric) / len(mood_numeric), 2)

    return render_template("index.html", entries_by_day=entries_by_day,
                           pending_tasks=pending_tasks, recent_tasks=recent_tasks,
                           completed_tasks=completed_tasks, chart_data=chart_data,
                           weekly_mood=weekly_mood)

@app.route("/submit_journal_ajax", methods=["POST"])
@login_required
def submit_journal_ajax():
    user_id = current_user.get_id()
    data = request.get_json()
    text = data["journal"]
    analysis = analyze_text(text)
    prod_score = custom_productivity_score(text)
    
    entry_id = add_entry(user_id, datetime.now().strftime('%Y-%m-%d'), text, analysis['mood'], prod_score)
    tasks = extract_tasks(text)
    if entry_id and tasks:
        for task in tasks:
            add_task(user_id, entry_id, task)
    return jsonify({"mood": analysis['mood'], "productivity": prod_score, "date": datetime.now().strftime('%Y-%m-%d'), "tasks": tasks})

@app.route('/complete_task/<string:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    user_id = current_user.get_id()
    try:
        update_task_status(user_id, task_id, True)
        return jsonify({"success": True, "message": "Task marked as complete."}), 200
    except Exception as e:
        print(f"Error completing task: {e}")
        return jsonify({"success": False, "message": "Error updating task."}), 500

@app.route("/api/chart_data/<period>")
@login_required
def api_chart_data(period):
    user_id = current_user.get_id()
    # Note: execute_aggregation needs to be user-aware
    # The logic in db.py for this function was updated to prepend the user_id match
    group_id, limit = None, 0
    if period == "daily":
        group_id, limit = "$date", 30
    elif period == "weekly":
        group_id, limit = {"$dateToString": {"format": "%Y-W%U", "date": {"$toDate": "$date"}}}, 12
    elif period == "monthly":
        group_id, limit = {"$substr": ["$date", 0, 7]}, 12
    else:
        return jsonify({"error": "Invalid period"}), 400
    
    pipeline = [
        {"$addFields": {"mood_numeric": {"$switch": {"branches": [{"case": {"$eq": ["$mood", "positive"]}, "then": 1}, {"case": {"$eq": ["$mood", "negative"]}, "then": -1}], "default": 0}}}},
        {"$group": {"_id": group_id, "avg_productivity": {"$avg": "$productivity"}, "avg_mood": {"$avg": "$mood_numeric"}}},
        {"$sort": {"_id": -1}}, {"$limit": limit}, {"$sort": {"_id": 1}},
        {"$project": {"label": "$_id", "productivity": {"$ifNull": ["$avg_productivity", 0]}, "mood": {"$ifNull": ["$avg_mood", 0]}, "_id": 0}}
    ]
    results = execute_aggregation(user_id, 'entries', pipeline)
    for row in results:
        row["productivity"] = round(row["productivity"], 2)
        row["mood"] = round(row["mood"], 2)
    return jsonify(results)

@app.route('/day_view/<date>')
@login_required
def day_view(date):
    user_id = current_user.get_id()
    entries = get_entries_and_tasks_for_date(user_id, date)
    return render_template('day_view.html', date=date, entries=entries)

@app.route('/delete_entries', methods=['POST'])
@login_required
def delete_entries():
    user_id = current_user.get_id()
    entry_ids = request.form.getlist('entry_ids')
    date = request.form.get('date')
    if entry_ids:
        delete_entries_and_tasks(user_id, entry_ids)
    return redirect(url_for('day_view', date=date))

if __name__ == "__main__":
    app.run(debug=True)



# from flask import Flask, render_template, request, jsonify
# from flask import request, redirect, url_for
# from nlp.analysis import analyze_text
# from nlp.task_extractor import extract_tasks
# from scorer import custom_productivity_score
# # import sqlite3
# from datetime import datetime
# import os
# from collections import defaultdict
# from flask import redirect, url_for
# from database.db import (
#     init_db, add_entry, add_task, update_task_status,
#     get_all_entries_sorted_asc, get_pending_tasks, 
#     get_tasks_with_entry_info, get_chart_data, get_tasks_for_entry_ids,
#     execute_aggregation,get_entries_and_tasks_for_date,
#     delete_entries_and_tasks
# )

# app = Flask(__name__)

# init_db() 

# @app.route("/", methods=["GET"])
# def index():
#     # --- 1. Fetch all data using the new DB functions from db.py ---
#     # This block replaces all the c.execute() calls
#     raw_entries = get_all_entries_sorted_asc()
#     pending_tasks = get_pending_tasks()
#     recent_tasks = get_tasks_with_entry_info(completed_status=None, limit=5)
#     completed_tasks = get_tasks_with_entry_info(completed_status=True, limit=5)
#     chart_data = get_chart_data(limit=30)
    
#     # --- 2. Process data in Python (logic remains the same) ---
#     # The logic below is identical to your original, just adapted
#     # for the dictionary format from MongoDB instead of tuples.
    
#     grouped = defaultdict(list)
#     for entry in raw_entries:
#         # Accessing by key instead of index: entry['date'] instead of entry[0]
#         grouped[entry['date']].append(entry)

#     entries_by_day = []
#     mood_score_map = {"negative": -1, "neutral": 0, "positive": 1}

#     # Efficiently fetch all tasks in one go to avoid querying in a loop
#     all_entry_ids = [entry['_id'] for entry in raw_entries]
#     all_tasks = get_tasks_for_entry_ids(all_entry_ids)
    
#     tasks_by_entry_id = defaultdict(list)
#     for task in all_tasks:
#         tasks_by_entry_id[task['entry_id']].append(task['task_text'])

#     for date, items in grouped.items():
#         # Accessing by key: e['mood'] instead of e[2], e['productivity'] instead of e[3]
#         moods = [e['mood'] for e in items]
#         prod_scores = [e['productivity'] for e in items]
#         mood_numeric = [mood_score_map.get(m, 0) for m in moods]

#         avg_mood_score = sum(mood_numeric) / len(mood_numeric) if mood_numeric else 0
#         avg_prod_score = sum(prod_scores) / len(prod_scores) if prod_scores else 0
        
#         numbered_entries = list(enumerate(items, start=1))

#         # Reconstruct the tasks for the day from our efficiently fetched list
#         tasks_for_day = []
#         for entry in items:
#             # Accessing by key: entry['_id'] instead of entry[0]
#             entry_id = entry['_id']
#             tasks_for_day.append({
#                 "entry_id": entry_id,
#                 "tasks": tasks_by_entry_id.get(entry_id, [])
#             })

#         entries_by_day.append({
#             "date": date,
#             "avg_mood_score": round(avg_mood_score, 2),
#             "avg_productivity": round(avg_prod_score, 2),
#             "entries": numbered_entries,
#             "tasks_for_day": tasks_for_day
#         })

#     entries_by_day.sort(key=lambda x: x["date"])

#     weekly_mood = {}
#     for date, items in grouped.items():
#         moods = [e['mood'] for e in items]
#         mood_numeric = [mood_score_map.get(m, 0) for m in moods]
#         if mood_numeric:
#             weekly_mood[date] = round(sum(mood_numeric) / len(mood_numeric), 2)

#     # NO conn.close() or sqlite3 code is needed anymore.

#     return render_template("index.html",
#                            entries_by_day=entries_by_day,
#                            pending_tasks=pending_tasks,
#                            recent_tasks=recent_tasks,
#                            completed_tasks=completed_tasks,
#                            chart_data=chart_data,
#                            weekly_mood=weekly_mood)
# @app.route("/submit_journal_ajax", methods=["POST"])
# def submit_journal_ajax():
#     data = request.get_json()
#     text = data["journal"]
#     analysis = analyze_text(text)

#     # Use your custom productivity calculation here
#     prod_score = custom_productivity_score(text)

#     # --- REPLACED SQLITE BLOCK ---
#     # Call the add_entry function, which handles the MongoDB connection
#     entry_id = add_entry(
#         datetime.now().strftime('%Y-%m-%d'), # Storing date as string is common
#         text, 
#         analysis['mood'], 
#         prod_score
#     )
    
#     tasks = extract_tasks(text)
#     if entry_id and tasks: # Make sure the entry was created before adding tasks
#         for task in tasks:
#             # Call the add_task function for each task
#             add_task(entry_id, task)
#     # --- END OF REPLACED BLOCK ---

#     return jsonify({
#         "mood": analysis['mood'],
#         "productivity": prod_score,
#         "date": datetime.now().strftime('%Y-%m-%d'),
#         "tasks": tasks
#     })

# # Note: The task_id type is changed from <int:task_id> to <string:task_id>
# # because MongoDB uses string ObjectIds, not integers.
# @app.route('/complete_task/<string:task_id>', methods=['POST'])
# def complete_task(task_id):
#     try:
#         # Try to update task status in database
#         update_task_status(task_id, True)
#     except Exception as e:
#         # Log any backend issue
#         print(f"[ERROR] Failed to update task {task_id}: {e}")

#     # ✅ Always return a success response so frontend always gets a consistent message
#     return jsonify({
#         "success": True,
#         "message": "Task marked as complete."
#     }), 200



# @app.route("/api/chart_data/<period>")
# def api_chart_data(period):
#     """Provides chart data aggregated by daily, weekly, or monthly periods."""
    
#     group_id = None
#     limit = 0
    
#     # Determine the grouping logic and limit based on the period
#     if period == "daily":
#         group_id = "$date"
#         limit = 30
#     elif period == "weekly":
#         # Groups by a "YYYY-W##" string format, e.g., "2025-W36"
#         group_id = {"$dateToString": {"format": "%Y-W%U", "date": {"$toDate": "$date"}}}
#         limit = 12
#     elif period == "monthly":
#         # Groups by a "YYYY-MM" string format, e.g., "2025-09"
#         group_id = {"$substr": ["$date", 0, 7]}
#         limit = 12
#     else:
#         return jsonify({"error": "Invalid period"}), 400

#     # The aggregation pipeline (the "logic") is now built here in the route
#     pipeline = [
#         # Stage 1: Add a temporary field for numeric mood score
#         {"$addFields": {"mood_numeric": {"$switch": {"branches": [{"case": {"$eq": ["$mood", "positive"]}, "then": 1}, {"case": {"$eq": ["$mood", "negative"]}, "then": -1}], "default": 0}}}},
        
#         # Stage 2: Group by the chosen period and calculate averages
#         {"$group": {"_id": group_id, "avg_productivity": {"$avg": "$productivity"}, "avg_mood": {"$avg": "$mood_numeric"}}},
        
#         # Stage 3: Sort by the group label (date/week/month) descending to get the most recent
#         {"$sort": {"_id": -1}},
        
#         # Stage 4: Limit the number of results
#         {"$limit": limit},

#         # Stage 5: Sort again ascending for correct chart order
#         {"$sort": {"_id": 1}},
        
#         # Stage 6: Reshape the output document to the desired format
#         {"$project": {"label": "$_id", "productivity": {"$ifNull": ["$avg_productivity", 0]}, "mood": {"$ifNull": ["$avg_mood", 0]}, "_id": 0}}
#     ]
    
#     # Call the generic aggregation function from db.py
#     results = execute_aggregation('entries', pipeline)
    
#     # Round the numbers for clean presentation
#     for row in results:
#         row["productivity"] = round(row["productivity"], 2)
#         row["mood"] = round(row["mood"], 2)

#     return jsonify(results)

# @app.route('/day_view/<date>')
# def day_view(date):
#     # This one line replaces all the old database code and the loop.
#     entries = get_entries_and_tasks_for_date(date)

#     return render_template('day_view.html', date=date, entries=entries)

# @app.route('/delete_entries', methods=['POST'])
# def delete_entries():
#     # Get list of selected entry IDs from the form
#     entry_ids = request.form.getlist('entry_ids')
#     date = request.form.get('date')  # Get the date from the hidden input
#     print(f"[DEBUG] Received entry_ids for deletion: {entry_ids}")
#     if entry_ids:
#         delete_entries_and_tasks(entry_ids)
#     else:
#         print("[DEBUG] No entry_ids received for deletion.")
#     # Redirect back to the day view page for the same date
#     return redirect(url_for('day_view', date=date))


# if __name__ == "__main__":
#     init_db()
#     app.run(debug=True)
