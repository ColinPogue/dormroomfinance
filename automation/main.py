#!/usr/bin/env python3
"""
DormRoomFinance Automation
Runs daily via launchd:
1. Picks next keyword from list
2. Writes article via Claude API
3. Publishes to GitHub (triggers GitHub Pages rebuild)
4. Sends email notification
"""

import json
import os
import sys
from datetime import date
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)

from keyword_picker import pick_next_keyword
from article_writer import write_article
from publisher import publish_article
from notifier import send_notification

LAST_RUN_FILE = os.path.join(os.path.dirname(__file__), "last_run.json")


def already_ran_today():
    if not os.path.exists(LAST_RUN_FILE):
        return False
    with open(LAST_RUN_FILE) as f:
        data = json.load(f)
    return data.get("last_run_date") == str(date.today())


def mark_ran_today():
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run_date": str(date.today())}, f)


def main():
    print("=== DormRoomFinance Daily Run ===")

    if already_ran_today():
        print("Already ran today — skipping.")
        return

    # Step 1: Pick keyword
    print("Picking next keyword...")
    keyword_entry = pick_next_keyword()
    print(f"  Keyword: {keyword_entry['keyword']}")
    print(f"  Category: {keyword_entry['category']}")

    # Step 2: Write article
    print("Writing article with Claude...")
    content, slug, keyword, category = write_article(keyword_entry)
    print(f"  Article written: {slug}")

    # Step 3: Publish to GitHub
    print("Publishing to GitHub...")
    success, result = publish_article(content, slug)
    if not success:
        print(f"  ERROR publishing: {result}")
        sys.exit(1)
    print(f"  Published: {result}")

    # Step 4: Get total article count
    progress_file = os.path.join(os.path.dirname(__file__), "progress.json")
    with open(progress_file) as f:
        progress = json.load(f)
    total = progress["total_articles"]

    mark_ran_today()

    # Step 5: Send notification
    print("Sending email notification...")
    try:
        send_notification(keyword, category, result, total)
    except Exception as e:
        print(f"  WARNING: Notification failed: {e}")

    print(f"=== Done. Article #{total} published. ===")


if __name__ == "__main__":
    main()
