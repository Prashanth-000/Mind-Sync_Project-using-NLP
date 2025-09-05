M I N D S Y N C · J O U R N A L 🧠
MindSync is an intelligent web application designed to help you understand your thoughts, track your productivity, and gain insights into your daily life through smart journaling.

About The Project
In a fast-paced world, taking a moment for self-reflection is more important than ever. MindSync was built to be more than just a digital diary; it's a personal data analyst that helps you connect with your inner world. By leveraging Natural Language Processing (NLP), the application goes beyond simple text storage to provide users with actionable, data-driven insights into their mental well-being and daily productivity patterns.

The goal of this project is to create a secure, intuitive, and insightful tool that empowers users to recognize patterns in their thoughts and behaviors. Whether you're looking to understand your emotional triggers, track progress towards a goal, or simply get a clearer picture of your day-to-day life, MindSync provides the tools to help you on your journey of personal growth.

✨ Key Features
Feature

Description

🧠 AI-Powered Analysis

Automatically analyzes the sentiment of each entry to determine if the mood is positive, neutral, or negative, and calculates a dynamic productivity score based on the language used.

✅ Automatic Tasks

Intelligently scans your writing for phrases indicating a to-do item (e.g., "I need to...") and automatically extracts them into a clean, manageable pending task list.

🔐 Secure Authentication

A complete user login and registration system, featuring robust password hashing with Bcrypt, ensures that your journal entries are always private and accessible only to you.

📊 Data Visualization

Features a dynamic, interactive line chart that beautifully tracks your mood and productivity trends over daily, weekly, and monthly periods, helping you visualize your progress.

🗓️ Journal Management

A dedicated "Day View" allows you to easily review all entries and tasks for a specific date, with the ability to select and delete multiple entries at once.

🚀 Modern UI

A clean, professional, and fully responsive interface built with Bootstrap 5 provides a seamless and intuitive experience on both desktop and mobile devices.

🛠️ Tech Stack
Frontend: HTML5 | CSS3 | JavaScript | Bootstrap 5 | Chart.js

Backend: Python | Flask

Database: MongoDB (via MongoDB Atlas)

NLP & Analysis: TextBlob | NLTK

Authentication: Flask-Login | Flask-Bcrypt

🚀 Getting Started
Follow these instructions to get the project up and running on your local machine.

Prerequisites
Python 3.10+ and pip installed.

A free MongoDB Atlas account to host the database.

git installed on your machine for cloning the repository.

Installation & Setup
Clone the Repository:
Open your terminal and clone the project code to your local machine.

git clone [https://github.com/Prashanth-000/Mind-Sync_Project-using-NLP](https://github.com/Prashanth-000/Mind-Sync_Project-using-NLP)
cd mindsync-journal

Set Up a Virtual Environment:
It is a critical best practice to isolate project dependencies to avoid conflicts with other projects.

# Windows
python -m venv venv && .\venv\Scripts\activate
# macOS/Linux
python3 -m venv venv && source venv/bin/activate

Install Dependencies:
This command reads the requirements.txt file and installs all necessary Python libraries for the project.

pip install -r requirements.txt

Configure Environment Variables:

Create a file named .env in the project root. This file will securely store your database credentials and is ignored by Git.

Log in to your MongoDB Atlas account, navigate to your cluster, and click "Connect". Select "Connect your application" and copy the connection string.

Add this string to your .env file, replacing <password> with your database user's password:

MONGO_CLUSTER_URL="mongodb+srv://<user>:<password>@cluster-url.mongodb.net/?retryWrites=true&w=majority"

(Optional) Seed the Database with Sample Data:

To quickly see the app's features in action, you can run the provided seeding script. This will create a pre-populated test user (test@example.com) and fill their account with 7 days of sample entries and tasks.

python seed_user_data.py

Run the Application:
Start the Flask development server.

flask run

You should see output in your terminal confirming a successful connection to MongoDB. The application will be live at http://127.0.0.1:5000.

Architectural Overview
The application follows a standard client-server architecture, with a clear separation of concerns:

Frontend (Client): The user interacts with responsive HTML pages rendered by Flask's Jinja2 templating engine. Client-side JavaScript is used to create a dynamic, single-page-like experience for features like real-time task completion and fetching chart data from API endpoints without requiring a full page reload.

Backend (Server): The Flask application serves as the central hub. It handles all incoming requests, manages user authentication and sessions, processes business logic, and exposes a JSON API for the frontend to consume.

NLP Layer: When a user submits an entry, the backend passes the text to the dedicated nlp module. Here, a pipeline of functions analyzes the text for sentiment using libraries like TextBlob and NLTK, extracts potential tasks using regular expressions, and calculates a productivity score based on keyword analysis.

Database: The original text and all the extracted metadata (mood, productivity, tasks) are stored as documents in MongoDB collections. Each document is securely linked to the user's unique user_id, ensuring strict data privacy and isolation between user accounts. The NoSQL nature of MongoDB provides the flexibility to easily evolve the data schema in the future.

🔮 Future Enhancements
This project has a strong foundation that can be extended with more advanced features:

Advanced Topic Modeling: Go beyond simple mood to identify and track key topics in a user's life (e.g., "work," "family," "health") using techniques like Latent Dirichlet Allocation (LDA). This would allow users to see how their mood correlates with different aspects of their life.

AI-Powered Summaries: Integrate a generative AI model (like the Gemini API) to provide users with weekly summaries and encouraging, personalized insights. For example, the system could generate a message like, "It seems like you felt most productive on days you wrote about your creative projects. Great job!"

Custom Reminders: Allow users to set email or push notification reminders (e.g., "Don't forget to write in your journal today!") to encourage consistent journaling habits.

Full-Text Search: Implement a powerful search feature using MongoDB's built-in text indexing capabilities. This would allow users to easily find past entries by searching for specific keywords or phrases.

📂 Project Structure
├── nlp/
│   ├── analysis.py         # Handles sentiment analysis
│   ├── task_extractor.py   # Extracts tasks from text
│   └── scorer.py           # Calculates productivity score
├── templates/
│   ├── index.html          # Main dashboard
│   ├── day_view.html       # View entries for a specific day
│   ├── login.html          # User login page
│   ├── register.html       # User registration page
│   └── layout.html         # Base template with navbar
├── app.py                  # Main Flask application file
├── database/
│   └── db.py               # All MongoDB logic and functions
├── models.py               # User model for Flask-Login
├── seed_user_data.py       # Script to populate the DB
├── requirements.txt        # Project dependencies
└── README.md               # You are here!
