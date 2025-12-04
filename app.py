import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from collections import defaultdict
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from insights import generate_insights
from nlp.analysis import analyze_text
from nlp.task_extractor import extract_tasks
from nlp.scorer import custom_productivity_score
from flask_mail import Mail, Message
from nlp.summarizer import generate_rule_based_summary
from database.db import get_entries_for_period
import threading
from werkzeug.utils import secure_filename
from nlp.media_analyzer import transcribe_audio_local
from prompts import generate_prompt
import subprocess


app = Flask(__name__)


app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app) 
from database.db import (
    init_db, add_entry, add_task, update_task_status,
    get_all_entries_sorted_asc, get_pending_tasks, 
    get_tasks_with_entry_info, get_chart_data, get_tasks_for_entry_ids,
    execute_aggregation, get_entries_and_tasks_for_date,
    delete_entries_and_tasks
)
from models import User

app.config['SECRET_KEY'] = 'a_very_secret_and_long_random_string_for_security'

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to load the current user from the database."""
    return User.find_by_id(user_id)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'

init_db() 

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

    weekly_mood = {}  
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
@app.route("/api/send_report", methods=['POST'])
@login_required
def send_report():
    data = request.get_json()
    summary = data.get('summary')
    if not summary:
        return jsonify({"success": False, "error": "No summary data provided."}), 400

    recipient = os.getenv('HEALTHCARE_CENTER_EMAIL')
    if not recipient:
        return jsonify({"success": False, "error": "Recipient email is not configured."}), 500
        
    user_email = current_user.email
    subject = f"MindSync Wellness Report for User: {user_email}"

    # Format the JSON summary into a clean HTML email
    html_body = f"""
    <html>
        <body>
            <h2>MindSync AI Wellness Summary for {user_email}</h2>
            <h3>Positive Aspects</h3>
            <ul>{''.join([f'<li>{item}</li>' for item in summary.get("positive_aspects", [])])}</ul>
            <h3>Areas for Reflection</h3>
            <ul>{''.join([f'<li>{item}</li>' for item in summary.get("negative_aspects", [])])}</ul>
            <h3>Improvement Tips</h3>
            <ul>{''.join([f'<li>{item}</li>' for item in summary.get("improvement_tips", [])])}</ul>
            <h3>Other Insights</h3>
            <ul>{''.join([f'<li>{item}</li>' for item in summary.get("other_factors", [])])}</ul>
        </body>
    </html>
    """
    
    try:
        msg = Message(subject, recipients=[recipient], html=html_body)
        mail.send(msg)
        return jsonify({"success": True, "message": "Report sent successfully!"})
    except Exception as e:
        print(f"Failed to send email: {e}")
        return jsonify({"success": False, "error": "Failed to send the report."}), 500
    
@app.route("/api/get_summary/<string:period>")
@login_required
def get_summary(period):
    days = 0
    if period == 'day':
        days = 1
    elif period == 'week':
        days = 7
    else:
        return jsonify({"error": "Invalid period specified."}), 400

    user_id = current_user.get_id()
     
    entries = get_entries_for_period(user_id, days=days)

    summary_data = generate_rule_based_summary(entries)
    
    if "error" in summary_data:
        return jsonify(summary_data), 500
        
    return jsonify(summary_data)

# This is the helper function that will run in the background
def run_audio_analysis_background(file_path, user_id):
    """A wrapper function to run the full audio analysis pipeline in a background thread."""
    print(f"BACKGROUND THREAD: Starting audio analysis for {file_path}")
    
    # 1. Transcribe the audio to text
    transcribed_text = transcribe_audio_local(file_path)
    
    if transcribed_text:
        # 2. Run your EXISTING NLP analysis on the transcribed text
        analysis = analyze_text(transcribed_text)
        tasks = extract_tasks(transcribed_text)
        
        # 3. Create a new journal entry in the database with the results
        # This makes the audio entry appear just like a written one
        add_entry(
            user_id,
            datetime.now().strftime('%Y-%m-%d'),
            f"(Audio Journal Entry)\n\n{transcribed_text}", # Mark it as an audio entry
            analysis['mood'],
            custom_productivity_score(transcribed_text) # Use your existing scorer
        )
        
        # Optional: You could add the extracted tasks to the database as well.
        print(f"--- BACKGROUND ANALYSIS COMPLETE (for User {user_id}) ---")
        print(f"  > Mood: {analysis['mood']}, Tasks: {len(tasks)}")
    else:
        print(f"--- BACKGROUND ANALYSIS FAILED: No text transcribed. ---")

    os.remove(file_path)

@app.route("/api/analyze_audio", methods=['POST'])
@login_required
def analyze_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Only allow WAV files
    if not file.filename.lower().endswith(".wav"):
        return jsonify({"error": "Only WAV files are supported"}), 400

    filename = secure_filename(file.filename)
    temp_dir = os.path.join(app.root_path, 'temp_uploads')
    os.makedirs(temp_dir, exist_ok=True)

    temp_file_path = os.path.abspath(os.path.join(temp_dir, filename))
    file.save(temp_file_path)

    print(f"File saved at: {temp_file_path}, exists? {os.path.exists(temp_file_path)}")

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        import threading
        threading.Thread(
            target=run_audio_analysis_background,
            args=(temp_file_path, current_user.get_id()),
            daemon=True
        ).start()
    else:
        run_audio_analysis_background(temp_file_path, current_user.get_id())

    return jsonify({
        "message": "Audio file has been successfully analyzed and saved as a new journal entry."
    }), 200


# Route to get a journal prompt
@app.route("/api/get_prompt")
def get_prompt_api():
    """Generates a personalized journaling prompt."""
    try:
        user_id = None
        if current_user.is_authenticated:
            user_id = str(current_user.id)

        prompt = generate_prompt(user_id)
        return jsonify({"prompt": prompt})
    except Exception as e:
        import traceback
        print("❌ Error generating prompt:")
        traceback.print_exc()
        return jsonify({"prompt": "Error generating prompt."}), 500
@app.route('/insights')
def insights_redirect():
    return redirect(url_for('insights_page', period='weekly'))


@app.route('/insights/<period>')
def insights_page(period):
    # Check for valid periods to be safe
    if period not in ['weekly', 'monthly', 'all']:
        return "Invalid period selected.", 404

    # Pass the period from the URL to our upgraded function
    insights_list = generate_insights(period=period)
    
    # Also pass the period to the template so we can display it in the title
    return render_template('insights.html', insights=insights_list, period=period)

@app.route("/record_audio", methods=["POST"])
def record_audio():
    # Run your external recording script
    subprocess.Popen(["python", "audio_recorder.py"])
    return "Recording started!"

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

