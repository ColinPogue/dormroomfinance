import json
import os

KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "keywords.json")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "progress.json")


def pick_next_keyword():
    with open(KEYWORDS_FILE) as f:
        data = json.load(f)
    keywords = data["keywords"]

    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

    next_index = progress["last_index"] + 1

    if next_index >= len(keywords):
        # Cycled through all keywords — start over
        next_index = 0

    keyword_entry = keywords[next_index]

    # Update progress
    progress["last_index"] = next_index
    progress["completed"].append(keyword_entry["keyword"])
    progress["total_articles"] += 1

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

    return keyword_entry
