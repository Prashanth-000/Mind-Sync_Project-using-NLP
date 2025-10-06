import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Important: This script should be in the root directory of your project
# so it can correctly import from your other files.
from database.db import init_db, add_entry, add_task, find_user_by_email
from models import User


def seed_data_for_user():
    """
    Creates a specific test user (if they don't exist) and populates their
    account with 7 days of dummy journal entries and tasks.
    """
    print("--- Starting User-Specific Database Seeding ---")
    
    # Initialize the database connection
    init_db()

    # --- Step 1: Find or Create the Test User ---
    user = User.find_by_email(TEST_USER_EMAIL)
    if not user:
        print(f"Creating new test user: {TEST_USER_EMAIL}")
        User.create(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        user = User.find_by_email(TEST_USER_EMAIL)
        if not user:
            print("FATAL: Could not create or find the test user. Aborting.")
            return
    else:
        print(f"Found existing test user: {TEST_USER_EMAIL}")

    user_id = user.get_id()
    print(f"Seeding data for User ID: {user_id}")

    # --- Step 2: Define Dummy Data Pools ---
    sample_texts = [
        "Focused on the Q3 report and finalized the data visualization charts.",
        "A productive day. Managed to clear out my entire backlog of pending tasks.",
        "Team meeting went on longer than expected, which pushed back my afternoon schedule.",
        "Read a fascinating article on AI ethics. It gave me a lot to think about for our project.",
        "Felt a bit under the weather, so I took it easy and focused on minor administrative tasks.",
        "Completed the first draft of the user documentation. It's ready for review.",
        "Brainstormed with the design team. The new UI mockups look fantastic.",
        "Spent the day learning a new Python library for data analysis. It was challenging but rewarding."
    ]
    sample_tasks = [
        "Finalize Q3 report figures", "Deploy staging server update", "Review user feedback tickets",
        "Prepare agenda for weekly sync", "Draft project milestone summary",
        "Research competing products", "Create wireframes for new feature"
    ]
    moods = ["positive", "neutral", "negative"]

    # --- Step 3: Generate Data for the Last 7 Days ---
    today = datetime.now()
    for i in range(7):
        current_date = today - timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        num_entries_for_day = random.randint(1, 2)
        print(f"\nGenerating {num_entries_for_day} entries for {date_str}...")

        for _ in range(num_entries_for_day):
            entry_text = random.choice(sample_texts)
            entry_mood = random.choice(moods)
            entry_productivity = round(random.uniform(0.2, 0.9), 2)
            
            # Create a journal entry FOR THE SPECIFIC USER
            entry_id = add_entry(user_id, date_str, entry_text, entry_mood, entry_productivity)
            
            if entry_id:
                print(f"  > Created entry for user '{user.email}'.")
                
                num_tasks = random.randint(0, 3)
                if num_tasks > 0:
                    for _ in range(num_tasks):
                        task_text = random.choice(sample_tasks)
                        # Add tasks FOR THE SPECIFIC USER
                        add_task(user_id, entry_id, task_text)
                    print(f"    - Added {num_tasks} tasks to this entry.")
            else:
                print("  > FAILED to create entry.")

    print("\n--- User-Specific Database Seeding Complete ---")
    print(f"\nYou can now log in with:\nEmail: {TEST_USER_EMAIL}\nPassword: {TEST_USER_PASSWORD}")

if __name__ == "__main__":
    # Ensure environment variables are loaded for the script
    load_dotenv()
    seed_data_for_user()
