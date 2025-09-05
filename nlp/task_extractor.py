import re

def extract_tasks(text):
    """
    Extracts potential tasks from text using a list of common patterns.
    """
    # Patterns to identify phrases that likely indicate a task
    task_patterns = [
        # Matches phrases like "need to do X", "must finish Y"
        r"\b(?:need to|have to|must|should|want to|planning to|plan to|aim to|try to)\s+(.*?)(?:[.!\n]|$)",
        # Matches phrases like "todo: Z" or "to-do: A"
        r"\b(?:to[- ]do|todo)[^\w]*(.*?)(?:[.!\n]|$)"
    ]
    tasks = []
    for pattern in task_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up the extracted task text
            task = match.strip().rstrip('.!')
            if task:
                tasks.append(task)
    return tasks
