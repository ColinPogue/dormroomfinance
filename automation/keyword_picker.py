import json
import os
import random

KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "keywords.json")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "progress.json")


def pick_next_keyword():
    with open(KEYWORDS_FILE) as f:
        data = json.load(f)
    keywords = data["keywords"]

    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

    completed = set(progress.get("completed", []))
    remaining = [k for k in keywords if k["keyword"] not in completed]

    # If all keywords used, start over
    if not remaining:
        remaining = keywords
        progress["completed"] = []

    keyword_entry = random.choice(remaining)
    return keyword_entry, progress


def mark_keyword_complete(keyword_entry, progress):
    progress["completed"].append(keyword_entry["keyword"])
    progress["total_articles"] += 1

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)
