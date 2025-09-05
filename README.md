# M I N D S Y N C · J O U R N A L 🧠

**MindSync** is an intelligent web application designed to help you understand your thoughts, track your productivity, and gain insights into your daily life through smart journaling.

---

## 📃 About The Project
In a fast-paced world, taking a moment for self-reflection is more important than ever. **MindSync** was built to be more than just a digital diary; it's a **personal data analyst** that helps you connect with your inner world.

By leveraging **Natural Language Processing (NLP)**, the application goes beyond simple text storage to provide **actionable, data-driven insights** into your mental well-being and daily productivity patterns.

> Whether you're looking to understand your emotional triggers, track progress towards a goal, or simply get a clearer picture of your day-to-day life, **MindSync** provides the tools to help you on your journey of personal growth.

---

## ✨ Key Features
| Feature | Description |
|----------|-------------|
| 🧠 **AI-Powered Analysis** | Automatically analyzes sentiment to determine mood (positive, neutral, negative) and calculates a **dynamic productivity score**. |
| ✅ **Automatic Tasks** | Scans entries for phrases like *"I need to..."* and extracts them into a **pending task list**. |
| 🔐 **Secure Authentication** | Robust **Bcrypt password hashing** with Flask-Login for privacy and security. |
| 📊 **Data Visualization** | Interactive **charts** showing mood & productivity trends over daily, weekly, and monthly periods. |
| 🗓 **Journal Management** | A dedicated **Day View** for reviewing, selecting, and deleting multiple entries. |
| 🚀 **Modern UI** | **Responsive design** built with Bootstrap 5 for seamless desktop and mobile experiences. |

---

## 🛠️ Tech Stack
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js  
- **Backend:** Python, Flask  
- **Database:** MongoDB (via MongoDB Atlas)  
- **NLP & Analysis:** TextBlob, NLTK  
- **Authentication:** Flask-Login, Flask-Bcrypt

---

## 🚀 Getting Started
Follow these steps to set up the project on your local machine.

### **Prerequisites**
Make sure you have:
- Python **3.10+** and **pip** installed.
- A free **MongoDB Atlas** account.
- **Git** installed.

### **Installation & Setup**

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/mindsync-journal.git
cd mindsync-journal
```

#### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv && .\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv && source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
MONGO_CLUSTER_URL="mongodb+srv://<user>:<password>@cluster-url.mongodb.net/?retryWrites=true&w=majority"
```
Replace `<user>` and `<password>` with your MongoDB credentials.

#### 5. (Optional) Seed the Database with Sample Data
```bash
python seed_user_data.py
```
> This creates a test user (`test@example.com`) and pre-populates their account with 7 days of entries and tasks.

#### 6. Run the Application
```bash
flask run
```
Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🌐 Architectural Overview

### **1. Frontend (Client)**
- Built using **Flask's Jinja2 templates**.
- Uses **AJAX** to fetch chart data dynamically.
- Fully responsive interface with Bootstrap.

### **2. Backend (Server)**
- Flask application handling:
  - Authentication
  - Session management
  - Business logic
  - REST API for chart data and tasks

### **3. NLP Layer**
- Sentiment analysis using **TextBlob & NLTK**.
- Task extraction using **regular expressions**.
- Productivity scoring based on keyword analysis.

### **4. Database (MongoDB)**
- Stores entries as documents.
- Each entry is linked to a unique `user_id`.
- Flexible schema for easy evolution.

---

## 🔮 Future Enhancements
- **Advanced Topic Modeling:** Identify key life themes using LDA (e.g., "work," "family," "health").
- **AI-Powered Summaries:** Weekly generated summaries and encouragement using LLM APIs.
- **Custom Reminders:** Push notifications & email reminders for journaling.
- **Full-Text Search:** Search past entries using MongoDB text indexes.

---

## 🗂️ Project Structure
```
├── nlp/
│   ├── analysis.py         # Handles sentiment analysis
│   ├── task_extractor.py   # Extracts tasks from text
│   └── scorer.py           # Calculates productivity score
├── templates/
│   ├── index.html          # Main dashboard
│   ├── day_view.html       # Day-specific entries view
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   └── layout.html         # Base template
├── app.py                  # Main Flask application
├── database/
│   └── db.py               # MongoDB functions
├── models.py               # Flask-Login user model
├── seed_user_data.py       # Seed script
├── requirements.txt        # Dependencies
└── README.md               # This file
```

---

## 💡 Final Notes
MindSync is designed to **empower personal growth** through actionable data insights. Its modular architecture ensures it can grow with future features like AI-driven analysis and smart reminders.

> *"Your journal is more than just words — it's a map of your mind."*

