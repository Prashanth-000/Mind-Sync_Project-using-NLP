from typing import Dict, Any, List
import statistics
import random


def generate_rule_based_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates an advanced, rule-based summary with deeper insights and
    personalized recommendations like movies, shows, books, and activities.

    Args:
        entries (List[Dict[str, Any]]): List of journal entry dictionaries.
            Each entry contains:
              - 'mood': str -> 'positive', 'neutral', or 'negative'
              - 'productivity': float between 0 and 1
              - 'tasks': list of dicts with {'task': str, 'completed': bool}

    Returns:
        Dict[str, Any]: Structured summary with feedback, stats, and recommendations.
    """

    # =========================
    # STEP 1. Handle empty input
    # =========================
    if not entries:
        return {
            "positive_aspects": [],
            "negative_aspects": [],
            "improvement_tips": [
                "No journal entries found. Start writing today to track your mood and productivity!"
            ],
            "recommendations": {
                "movies": ["The Secret Life of Walter Mitty", "Good Will Hunting"],
                "shows": ["The Mind, Explained (Netflix)", "Chef's Table"],
                "books": ["Atomic Habits by James Clear", "Deep Work by Cal Newport"],
                "activities": ["Take a 10-minute walk in nature", "Practice deep breathing for 5 minutes"]
            },
            "other_factors": []
        }

    # =========================
    # STEP 2. Collect data
    # =========================
    mood_counts = {"positive": 0, "neutral": 0, "negative": 0}
    productivity_scores = []
    total_tasks = 0
    completed_tasks = 0

    for entry in entries:
        mood = entry.get('mood', 'neutral').lower()
        productivity = float(entry.get('productivity', 0))

        # Count mood
        if mood in mood_counts:
            mood_counts[mood] += 1
        else:
            mood_counts["neutral"] += 1  # default to neutral if invalid mood given

        productivity_scores.append(productivity)

        # Count tasks
        tasks = entry.get('tasks', [])
        total_tasks += len(tasks)
        completed_tasks += sum(1 for t in tasks if t.get('completed', False))

    num_entries = len(entries)

    # =========================
    # STEP 3. Calculate stats
    # =========================
    avg_productivity = statistics.mean(productivity_scores) if productivity_scores else 0
    productivity_std_dev = (
        statistics.pstdev(productivity_scores) if len(productivity_scores) > 1 else 0
    )

    # Mood trend
    if mood_counts["positive"] > mood_counts["negative"]:
        mood_trend = "improving"
    elif mood_counts["negative"] > mood_counts["positive"]:
        mood_trend = "declining"
    else:
        mood_trend = "stable"

    # Mood balance score (positive - negative) / total
    mood_balance = (
        (mood_counts["positive"] - mood_counts["negative"]) / max(1, num_entries)
    )

    # Task completion rate
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Dominant mood
    dominant_mood = max(mood_counts, key=mood_counts.get)

    # =========================
    # STEP 4. Positive feedback
    # =========================
    positive_aspects = [
        f"You journaled {num_entries} times this period — great commitment to self-reflection!"
    ]

    if mood_counts["positive"] > 0:
        positive_aspects.append(
            f"You had {mood_counts['positive']} positive mood entries, showing resilience and optimism."
        )

    if avg_productivity > 0.7:
        positive_aspects.append(
            "Your productivity levels were consistently strong, reflecting great focus and discipline."
        )

    if task_completion_rate > 70:
        positive_aspects.append("You completed most of your planned tasks — excellent progress!")

    # =========================
    # STEP 5. Negative feedback
    # =========================
    negative_aspects = []

    if mood_counts["negative"] > 0:
        negative_aspects.append(
            f"You experienced {mood_counts['negative']} negative mood entries. "
            "Consider identifying triggers behind these challenging moments."
        )

    if avg_productivity < 0.4:
        negative_aspects.append("Low average productivity — try focusing on fewer high-priority tasks.")

    if productivity_std_dev > 0.3:
        negative_aspects.append(
            "Your productivity varied greatly, which may indicate inconsistent planning or burnout."
        )

    if task_completion_rate < 50 and total_tasks > 0:
        negative_aspects.append(
            "Many tasks were left incomplete — consider breaking goals into smaller, manageable steps."
        )

    # =========================
    # STEP 6. Improvement tips
    # =========================
    improvement_tips = []

    if mood_trend == "declining":
        improvement_tips.append(
            "Your mood trend is declining. Try gratitude journaling or engaging in a relaxing hobby like painting or cooking."
        )
    elif mood_trend == "improving":
        improvement_tips.append(
            "Your mood is improving — keep reinforcing activities that bring you fulfillment."
        )
    else:
        improvement_tips.append(
            "Your mood is stable. Consider exploring new activities to challenge yourself and grow."
        )

    if avg_productivity < 0.4:
        improvement_tips.append(
            "Productivity is low. Start with one high-impact task each day to build momentum."
        )

    if task_completion_rate < 50:
        improvement_tips.append(
            "Low task completion rate detected. Use a to-do list with 3 key tasks per day."
        )

    # =========================
    # STEP 7. Fun Recommendations
    # =========================
    def safe_random_choice(options, count=2):
        return random.sample(options, min(count, len(options)))

    movie_recommendations = {
        "positive": ["The Pursuit of Happyness", "Good Will Hunting", "The Secret Life of Walter Mitty"],
        "neutral": ["Inside Out", "The Social Network", "Julie & Julia"],
        "negative": ["Soul", "Silver Linings Playbook", "About Time"],
    }

    show_recommendations = {
        "positive": ["Chef's Table", "Abstract: The Art of Design", "The Mind, Explained"],
        "neutral": ["Explained", "Our Planet", "The Great British Bake Off"],
        "negative": ["Headspace Guide to Meditation", "Queer Eye", "Tidying Up with Marie Kondo"],
    }

    book_recommendations = {
        "positive": ["Atomic Habits by James Clear", "Deep Work by Cal Newport", "The Power of Now by Eckhart Tolle"],
        "neutral": ["Mindset by Carol Dweck", "Drive by Daniel Pink", "Grit by Angela Duckworth"],
        "negative": ["The Happiness Trap by Russ Harris", "Feeling Good by David Burns", "The Untethered Soul by Michael Singer"],
    }

    activity_recommendations = {
        "positive": [
            "Celebrate a win by treating yourself to a special meal.",
            "Go on a scenic walk to reflect on your progress.",
            "Host a fun game night with friends."
        ],
        "neutral": [
            "Declutter your workspace for mental clarity.",
            "Do a 15-minute body stretch or yoga session.",
            "Listen to upbeat music while doing light chores."
        ],
        "negative": [
            "Practice deep breathing for 5 minutes.",
            "Write down three things you're grateful for.",
            "Watch a light-hearted comedy to relax."
        ],
    }

    recommendations = {
        "movies": safe_random_choice(movie_recommendations[dominant_mood]),
        "shows": safe_random_choice(show_recommendations[dominant_mood]),
        "books": safe_random_choice(book_recommendations[dominant_mood]),
        "activities": safe_random_choice(activity_recommendations[dominant_mood]),
    }

    # =========================
    # STEP 8. Other key factors
    # =========================
    other_factors = [
        f"Average productivity: {avg_productivity:.2f}",
        f"Productivity consistency (lower = better): {productivity_std_dev:.2f}",
        f"Task completion rate: {task_completion_rate:.1f}%",
        f"Mood balance score: {mood_balance:.2f}",
        f"Dominant mood: {dominant_mood.capitalize()}",
        f"Overall mood trend: {mood_trend.capitalize()}",
    ]

    # =========================
    # STEP 9. Final structured output
    # =========================
    return {
        "positive_aspects": positive_aspects,
        "negative_aspects": negative_aspects,
        "improvement_tips": improvement_tips,
        "recommendations": recommendations,
        "other_factors": other_factors,
    }
