import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from your .env file
load_dotenv()

# MONGO_USER = os.getenv("MONGO_USER")
# MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_CLUSTER_URL = os.getenv("MONGO_CLUSTER_URL")

# This global variable will hold the database connection object
db = None

def init_db():
    """Initializes the connection to the MongoDB Atlas database."""
    global db
    if db is None:
        try:
            if not all([MONGO_CLUSTER_URL]):
                raise ValueError("Missing MongoDB credentials in your .env file.")

            # Safely encode the username and password
            # safe_user = quote_plus(MONGO_USER)
            # safe_password = quote_plus(MONGO_PASSWORD)
            
            # Build the full, safe MongoDB URI
            MONGO_URI = MONGO_CLUSTER_URL

            client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            
            db = client.journal_db
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            db = None

# --- BASIC CRUD FUNCTIONS (UNCHANGED) ---

def add_entry(date, text, mood, productivity):
    if db is None: return None
    entry_document = {"date": date, "text": text, "mood": mood, "productivity": productivity}
    result = db.entries.insert_one(entry_document)
    return result.inserted_id

def add_task(entry_id, task_text):
    if db is None: return None
    task_document = {"entry_id": entry_id, "task_text": task_text, "status": "pending", "completed": False}
    db.tasks.insert_one(task_document)

def update_task_status(task_id, completed):
    if db is None: return None
    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": completed}})

# --- NEW ADVANCED QUERY FUNCTIONS FOR THE INDEX PAGE ---

def get_all_entries_sorted_asc():
    """Retrieves all journal entries, sorted by date ascending."""
    if db is None: return []
    return list(db.entries.find({}).sort("date", 1)) # 1 for ascending

def get_pending_tasks():
    """Retrieves all tasks that are not completed."""
    if db is None: return []
    return list(db.tasks.find({"completed": False}))

def get_tasks_with_entry_info(completed_status=None, limit=5):
    """
    Replaces the SQL JOIN. Fetches tasks and includes the date from their parent entry.
    Can filter by completion status.
    """
    if db is None: return []
    pipeline = []

    # Optional stage to filter by completed or not completed
    if completed_status is not None:
        pipeline.append({"$match": {"completed": completed_status}})

    # Core stages to replicate the JOIN and shape the data
    pipeline.extend([
        {"$sort": {"_id": -1}}, # Sort by task creation time (desc) to get recent ones
        {"$limit": limit},
        {
            "$lookup": { # This is the JOIN
                "from": "entries",
                "localField": "entry_id",
                "foreignField": "_id",
                "as": "entry_info"
            }
        },
        {"$unwind": "$entry_info"}, # Deconstructs the entry_info array
        {
            "$project": { # Selects the final fields
                "_id": 0,
                "task_text": "$task_text",
                "date": "$entry_info.date"
            }
        }
    ])
    return list(db.tasks.aggregate(pipeline))

def get_chart_data(limit=30):
    """Replaces the SQL GROUP BY. Aggregates entries by date for chart data."""
    if db is None: return []
    pipeline = [
        {"$sort": {"date": -1}},
        {"$limit": limit},
        {
            # Add a temporary field for numeric mood score
            "$addFields": {
                "mood_numeric": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$mood", "positive"]}, "then": 1},
                            {"case": {"$eq": ["$mood", "negative"]}, "then": -1}
                        ],
                        "default": 0
                    }
                }
            }
        },
        {
            # Group by date and calculate averages
            "$group": {
                "_id": "$date",
                "avg_productivity": {"$avg": "$productivity"},
                "avg_mood": {"$avg": "$mood_numeric"}
            }
        },
        {"$sort": {"_id": 1}}, # Sort final results by date ascending
        {
            # Project to the final format for the chart
            "$project": {
                "date": "$_id",
                "avg_productivity": "$avg_productivity",
                "avg_mood": "$avg_mood",
                "_id": 0
            }
        }
    ]
    return list(db.entries.aggregate(pipeline))

def get_tasks_for_entry_ids(entry_ids):
    """Efficiently fetches all tasks for a given list of entry IDs."""
    if db is None or not entry_ids: return []
    return list(db.tasks.find({"entry_id": {"$in": entry_ids}}))

def execute_aggregation(collection_name, pipeline):
    """Executes a generic aggregation pipeline on a specified collection."""
    if db is None: return []
    collection = db[collection_name]
    return list(collection.aggregate(pipeline))

def get_entries_and_tasks_for_date(date):
    """
    Fetches all entries for a specific date and joins their associated tasks
    using an aggregation pipeline.
    """
    if db is None: return []
    pipeline = [
        # Stage 1: Filter entries by the specified date
        {"$match": {"date": date}},
        # Stage 2: Join with the tasks collection
        {
            "$lookup": {
                "from": "tasks",
                "localField": "_id",
                "foreignField": "entry_id",
                "as": "tasks_info"
            }
        },
        # Stage 3: Reshape the output to match the template's needs
        {
            "$project": {
                    "_id": 1,   # ✅ KEEP the _id field so we can pass it to the template
    "journal_text": "$text",
    "mood": "$mood",
    "productivity": "$productivity",
    "tasks": {
        "$map": {
            "input": "$tasks_info",
            "as": "task",
            "in": {
                "task_text": "$$task.task_text",
                "status": "$$task.status",
                "completed": "$$task.completed"
            }
                    }
                }
            }
        }
    ]
    return list(db.entries.aggregate(pipeline))

def delete_entries_and_tasks(entry_ids):
    """Deletes entries and their tasks more efficiently with better debugging."""
    if db is None or not entry_ids:
        print("DEBUG: Delete function called with no DB or no IDs.")
        return

    print(f"DEBUG: Received entry IDs: {entry_ids}")

    # Step 1: Validate and convert all IDs to ObjectId
    valid_object_ids = []
    for eid in entry_ids:
        if isinstance(eid, str) and len(eid) == 24:
            try:
                valid_object_ids.append(ObjectId(eid))
            except Exception as e:
                print(f"DEBUG: Invalid ID format '{eid}'. Skipping. Error: {e}")
        else:
            print(f"DEBUG: Invalid or empty ID received: '{eid}'. Skipping.")

    if not valid_object_ids:
        print("DEBUG: No valid ObjectIDs found after filtering.")
        return

    print(f"DEBUG: Attempting to delete with valid ObjectIDs: {valid_object_ids}")

    # Step 2: Delete associated tasks in one operation
    tasks_result = db.tasks.delete_many({"entry_id": {"$in": valid_object_ids}})
    
    # Step 3: Delete the entries themselves in one operation
    entries_result = db.entries.delete_many({"_id": {"$in": valid_object_ids}})

    # Step 4: Report the results
    print("--- Deletion Summary ---")
    print(f"  > Tasks deleted: {tasks_result.deleted_count}")
    print(f"  > Entries deleted: {entries_result.deleted_count}")

