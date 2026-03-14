#!/usr/bin/env python3
"""
DormRoomFinance Automation
Runs daily via launchd:
1. Validates environment
2. Picks next keyword from list
3. Writes article via Claude API (with retry)
4. Publishes to GitHub
5. Sends email notification
"""

import json
import os
import sys
from datetime import date
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)

from keyword_picker import pick_next_keyword, mark_keyword_complete
from article_writer import write_article
from publisher import publish_article
from notifier import send_notification, send_failure_notification

LAST_RUN_FILE = os.path.join(os.path.dirname(__file__), "last_run.json")

REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
    "GITHUB_USERNAME",
    "GITHUB_REPO",
    "GMAIL_ADDRESS",
    "GMAIL_APP_PASSWORD",
    "NOTIFICATION_EMAIL",
]


def validate_env():
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


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

    validate_env()

    if already_ran_today():
        print("Already ran today — skipping.")
        return

    keyword_entry = None
    progress = None

    try:
        # Step 1: Pick keyword
        print("Picking next keyword...")
        keyword_entry, progress = pick_next_keyword()
        print(f"  Keyword: {keyword_entry['keyword']}")
        print(f"  Category: {keyword_entry['category']}")

        # Step 2: Write article (retries handled inside write_article)
        print("Writing article with Claude...")
        content, slug, keyword, category = write_article(keyword_entry)
        print(f"  Article written: {slug}")

        # Step 3: Publish to GitHub
        print("Publishing to GitHub...")
        success, result = publish_article(content, slug)
        if not success:
            raise RuntimeError(f"Publishing failed: {result}")
        print(f"  Published: {result}")

        # Step 4: Mark keyword complete only after successful publish
        mark_keyword_complete(keyword_entry, progress)
        total = progress["total_articles"] + 1

        mark_ran_today()

        # Step 5: Send success notification
        print("Sending email notification...")
        try:
            send_notification(keyword, category, result, total)
        except Exception as e:
            print(f"  WARNING: Notification failed: {e}")

        print(f"=== Done. Article #{total} published. ===")

    except Exception as e:
        print(f"ERROR: Pipeline failed — {e}")
        try:
            kw = keyword_entry["keyword"] if keyword_entry else "unknown"
            send_failure_notification(kw, str(e))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
