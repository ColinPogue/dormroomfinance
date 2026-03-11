import base64
import os
import requests
from datetime import datetime


def publish_article(content, slug):
    token = os.environ["GITHUB_TOKEN"]
    username = os.environ["GITHUB_USERNAME"]
    repo = os.environ["GITHUB_REPO"]

    filename = f"content/posts/{slug}.md"
    url = f"https://api.github.com/repos/{username}/{repo}/contents/{filename}"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Add article: {slug}",
        "content": encoded,
        "branch": "main",
    }

    response = requests.put(url, json=payload, headers=headers)

    if response.status_code in (200, 201):
        article_url = f"https://dormroomfinance.com/posts/{slug}/"
        return True, article_url
    else:
        return False, response.json().get("message", "Unknown error")
