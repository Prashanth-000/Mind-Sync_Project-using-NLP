import random

def generate_insights(period="all"):
    """
    Temporary function to return random insights for testing the frontend.
    """
    topics = ["Work", "Health", "Exercise", "Sleep", "Mood", "Study", "Friends", "Hobby", "Food", "Travel"]
    
    insights = []
    for _ in range(5):  # generate 5 random insights
        topic = random.choice(topics)
        count = random.randint(1, 10)
        avg_mood = round(random.uniform(-1, 1), 2)  # between -1 (negative) and 1 (positive)
        avg_prod = round(random.uniform(0, 10), 2)  # productivity score
        
        insights.append({
            "topic": topic,
            "count": count,
            "avg_mood": avg_mood,
            "avg_prod": avg_prod
        })
    
    return insights

import re
# from collections import defaultdict
# import math
# from datetime import datetime, timedelta
# from database.db import db

# STOP_WORDS = [
#     'a', 'about', 'am', 'an', 'and', 'are', 'as', 'at', 'be', 'been',
#     'being', 'but', 'by', 'can', 'did', 'do', 'does', 'doing', 'don',
#     'for', 'from', 'had', 'has', 'have', 'having', 'he', 'her', 'him',
#     'his', 'i', 'if', 'in', 'is', 'it', 'its', 'just', 'me', 'my', 'myself',
#     'now', 'of', 'off', 'on', 'or', 'our', 'ours', 's', 'she', 'should',
#     'so', 't', 'that', 'the', 'their', 'them', 'then', 'these', 'they',
#     'this', 'those', 'to', 'too', 'was', 'we', 'were', 'what', 'which',
#     'who', 'whom', 'will', 'with', 'you', 'your', 'yours'
# ]

# def generate_insights(period="all"):
#     """
#     Analyzes entries using a TF-IDF algorithm to find the most important topics.
#     If no significant patterns, fallback to last 5 entries.
#     """
#     if db is None:
#         return []

#     # Build query
#     query = {}
#     if period == "weekly":
#         start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
#         query["date"] = {"$gte": start_date}
#     elif period == "monthly":
#         start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
#         query["date"] = {"$gte": start_date}

#     entries = list(db.entries.find(query).sort("date", -1))
#     if not entries:
#         # No entries at all
#         return []

#     # --- Preprocess documents ---
#     processed_docs = []
#     for entry in entries:
#         raw_text = entry.get('text', '') or ''
#         clean_text = re.sub(r'[^\w\s]', '', raw_text).lower()
#         words = [w for w in clean_text.split() if w not in STOP_WORDS]
#         processed_docs.append(words)

#     # --- Term Frequency (TF) ---
#     tf_scores = []
#     for doc in processed_docs:
#         doc_tf = defaultdict(int)
#         for word in doc:
#             doc_tf[word] += 1
#         for word in doc_tf:
#             doc_tf[word] = doc_tf[word] / len(doc) if len(doc) > 0 else 0
#         tf_scores.append(doc_tf)

#     # --- Inverse Document Frequency (IDF) ---
#     doc_count = len(processed_docs)
#     word_doc_counts = defaultdict(int)
#     all_words = set(word for doc in processed_docs for word in doc)
#     for word in all_words:
#         for doc in processed_docs:
#             if word in doc:
#                 word_doc_counts[word] += 1
#     idf_scores = {}
#     for word, count in word_doc_counts.items():
#         idf_scores[word] = math.log((1 + doc_count) / (1 + count)) + 1

#     # --- TF-IDF computation ---
#     tfidf_scores = defaultdict(float)
#     for i, doc in enumerate(processed_docs):
#         for word in doc:
#             tfidf_scores[word] += tf_scores[i][word] * idf_scores[word]

#     # Top 10 topics
#     top_topics = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:10]
#     top_topics = [word for word, score in top_topics]

#     # --- Build insights ---
#     insights = []
#     mood_map = {'positive': 1, 'neutral': 0, 'negative': -1}

#     for topic in top_topics:
#         related_entries = [e for e in entries if topic in (e.get('text') or '').lower()]
#         mention_count = len(related_entries)
#         if mention_count == 0:
#             continue
#         avg_mood = sum(mood_map.get(e.get('mood', 'neutral'), 0) for e in related_entries) / mention_count
#         avg_prod = sum(e.get('productivity', 0) for e in related_entries) / mention_count
#         insights.append({
#             'topic': topic,
#             'count': mention_count,
#             'avg_mood': avg_mood,
#             'avg_prod': avg_prod
#         })

#     # --- Fallback: No significant patterns found ---
#     if not insights:
#         fallback_entries = entries[:5]  # Last 5 entries
#         for entry in fallback_entries:
#             insights.append({
#                 'topic': 'General',
#                 'count': 1,
#                 'avg_mood': mood_map.get(entry.get('mood', 'neutral'), 0),
#                 'avg_prod': entry.get('productivity', 0)
#             })

#     return insights
