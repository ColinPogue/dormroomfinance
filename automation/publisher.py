import base64
import os
import requests


def _github_put(url, headers, payload):
    response = requests.put(url, json=payload, headers=headers)
    return response


def publish_article(content, slug):
    token = os.environ["GITHUB_TOKEN"]
    username = os.environ["GITHUB_USERNAME"]
    repo = os.environ["GITHUB_REPO"]

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Publish image first if it exists locally
    image_local = os.path.join(
        os.path.dirname(__file__), f"../static/images/posts/{slug}.jpg"
    )
    if os.path.exists(image_local):
        with open(image_local, "rb") as f:
            image_encoded = base64.b64encode(f.read()).decode("utf-8")
        image_url = f"https://api.github.com/repos/{username}/{repo}/contents/static/images/posts/{slug}.jpg"
        image_payload = {
            "message": f"Add cover image: {slug}",
            "content": image_encoded,
            "branch": "main",
        }
        img_resp = _github_put(image_url, headers, image_payload)
        if img_resp.status_code not in (200, 201):
            print(f"  WARNING: Image upload failed: {img_resp.json().get('message')}")

    # Publish article
    filename = f"content/posts/{slug}.md"
    url = f"https://api.github.com/repos/{username}/{repo}/contents/{filename}"
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"Add article: {slug}",
        "content": encoded,
        "branch": "main",
    }

    response = _github_put(url, headers, payload)

    if response.status_code in (200, 201):
        article_url = f"https://dormroomfinance.com/posts/{slug}/"
        return True, article_url
    else:
        return False, response.json().get("message", "Unknown error")
