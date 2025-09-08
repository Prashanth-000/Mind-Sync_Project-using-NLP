import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv
from urllib.parse import quote_plus
from datetime import datetime, timedelta


# Load environment variables from your .env file
load_dotenv()

MONGO_CLUSTER_URL = os.getenv("MONGO_CLUSTER_URL")
db = None

def init_db():
    """Initializes the connection to the MongoDB Atlas database."""
    global db
    if db is None:
        try:
            if not MONGO_CLUSTER_URL:
                raise ValueError("Missing MongoDB credentials in your .env file.")
            
            client = MongoClient(MONGO_CLUSTER_URL, server_api=ServerApi('1'))
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            db = client.journal_db
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            db = None

# --- NEW: User Management Functions ---
def find_user_by_email(email):
    """Finds a user document by their email."""
    if db is None: return None
    return db.users.find_one({"email": email})

def find_user_by_id(user_id):
    """Finds a user document by their _id."""
    if db is None: return None
    try:
        return db.users.find_one({"_id": ObjectId(user_id)})
    except:
        return None

def create_user(email, password_hash):
    """Inserts a new user document into the database."""
    if db is None: return None
    return db.users.insert_one({"email": email, "password": password_hash})

# --- UPDATED: All functions below now require a user_id for security ---

def add_entry(user_id, date, text, mood, productivity):
    if db is None: return None
    entry_document = {
        "user_id": ObjectId(user_id), 
        "date": date, 
        "text": text, 
        "mood": mood, 
        "productivity": productivity
    }
    result = db.entries.insert_one(entry_document)
    return result.inserted_id

def add_task(user_id, entry_id, task_text):
    if db is None: return None
    task_document = {
        "user_id": ObjectId(user_id),
        "entry_id": entry_id, 
        "task_text": task_text, 
        "status": "pending", 
        "completed": False
    }
    db.tasks.insert_one(task_document)

def update_task_status(user_id, task_id, completed):
    if db is None: return None
    # Security: Ensure the user owns the task they are trying to update
    db.tasks.update_one(
        {"_id": ObjectId(task_id), "user_id": ObjectId(user_id)}, 
        {"$set": {"completed": completed}}
    )

def get_all_entries_sorted_asc(user_id):
    if db is None: return []
    return list(db.entries.find({"user_id": ObjectId(user_id)}).sort("date", 1))

def get_pending_tasks(user_id):
    if db is None: return []
    return list(db.tasks.find({"user_id": ObjectId(user_id), "completed": False}))

def get_tasks_with_entry_info(user_id, completed_status=None, limit=5):
    if db is None: return []
    pipeline = [{"$match": {"user_id": ObjectId(user_id)}}] # Filter by user first
    if completed_status is not None:
        pipeline.append({"$match": {"completed": completed_status}})
    
    pipeline.extend([
        {"$sort": {"_id": -1}},
        {"$limit": limit},
        {"$lookup": {"from": "entries", "localField": "entry_id", "foreignField": "_id", "as": "entry_info"}},
        {"$unwind": "$entry_info"},
        {"$project": {"_id": 0, "task_text": "$task_text", "date": "$entry_info.date"}}
    ])
    return list(db.tasks.aggregate(pipeline))

def get_chart_data(user_id, limit=30):
    if db is None: return []
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}}, # Filter by user first
        {"$sort": {"date": -1}},
        {"$limit": limit},
        {"$addFields": {"mood_numeric": {"$switch": {"branches": [{"case": {"$eq": ["$mood", "positive"]}, "then": 1}, {"case": {"$eq": ["$mood", "negative"]}, "then": -1}], "default": 0}}}},
        {"$group": {"_id": "$date", "avg_productivity": {"$avg": "$productivity"}, "avg_mood": {"$avg": "$mood_numeric"}}},
        {"$sort": {"_id": 1}},
        {"$project": {"date": "$_id", "avg_productivity": "$avg_productivity", "avg_mood": "$avg_mood", "_id": 0}}
    ]
    return list(db.entries.aggregate(pipeline))

def get_tasks_for_entry_ids(user_id, entry_ids):
    if db is None or not entry_ids: return []
    return list(db.tasks.find({"user_id": ObjectId(user_id), "entry_id": {"$in": entry_ids}}))

def execute_aggregation(user_id, collection_name, pipeline):
    if db is None: return []
    # Prepend the user_id match to any pipeline for security
    full_pipeline = [{"$match": {"user_id": ObjectId(user_id)}}] + pipeline
    return list(db[collection_name].aggregate(full_pipeline))

def get_entries_and_tasks_for_date(user_id, date):
    if db is None: return []
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "date": date}}, # Filter by user first
        {"$lookup": {"from": "tasks", "localField": "_id", "foreignField": "entry_id", "as": "tasks"}},
        {"$project": {"_id": 1, "journal_text": "$text", "mood": "$mood", "productivity": "$productivity", "tasks": "$tasks"}}
    ]
    return list(db.entries.aggregate(pipeline))

def delete_entries_and_tasks(user_id, entry_ids):
    if db is None or not entry_ids: return

    valid_object_ids = [ObjectId(eid) for eid in entry_ids if eid and len(eid) == 24]
    if not valid_object_ids: return

    # Security: Ensure the queries include the user_id
    db.tasks.delete_many({"user_id": ObjectId(user_id), "entry_id": {"$in": valid_object_ids}})
    db.entries.delete_many({"user_id": ObjectId(user_id), "_id": {"$in": valid_object_ids}})

def get_entries_for_period(user_id, days=7):
    """Fetches all journal entries for a user within the last N days."""
    if db is None: return []
    start_date = datetime.now() - timedelta(days=days)
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    return list(db.entries.find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": start_date_str}
    }).sort("date", 1))

def save_summary_to_cache(user_id, period, summary_data):
    """Saves a generated summary to the 'summaries' collection with a timestamp."""
    if db is None: return
    db.summaries.update_one(
        {"user_id": ObjectId(user_id), "period": period},
        {"$set": {"summary": summary_data, "created_at": datetime.utcnow()}},
        upsert=True
    )

def get_summary_from_cache(user_id, period, max_age_hours=6):
    """Retrieves a summary from the cache if it's not too old."""
    if db is None: return None
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        return None
        
    cached = db.summaries.find_one({"user_id": user_obj_id, "period": period})
    
    if cached and 'created_at' in cached:
        cache_age = datetime.utcnow() - cached['created_at']
        if cache_age < timedelta(hours=max_age_hours):
            return cached.get('summary')
    return None


