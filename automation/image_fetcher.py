import os
import requests

PEXELS_API_KEY = None  # loaded from env at call time
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "../static/images/posts")

# Fallback search terms per category if keyword search returns nothing
CATEGORY_FALLBACKS = {
    "Credit Cards": "credit card wallet finance",
    "Investing": "stock market investing finance",
    "Budgeting": "budgeting money saving",
    "Side Hustles": "laptop working coffee freelance",
    "Student Loans": "college campus graduation student",
    "First Job Finances": "office work professional desk",
    "Banking": "bank money savings",
    "Saving Money": "piggy bank saving money",
}


def fetch_image(keyword, slug, category):
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        print("  WARNING: PEXELS_API_KEY not set, skipping image.")
        return None, None

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Try keyword first, then category fallback
    search_terms = [keyword, CATEGORY_FALLBACKS.get(category, "finance money college")]

    photo = None
    photographer = None

    for term in search_terms:
        result = _search_pexels(api_key, term)
        if result:
            photo, photographer = result
            break

    if not photo:
        print("  WARNING: No Pexels image found, skipping.")
        return None, None

    # Download and save image
    image_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
    img_data = requests.get(photo, timeout=15).content
    with open(image_path, "wb") as f:
        f.write(img_data)

    web_path = f"/images/posts/{slug}.jpg"
    return web_path, photographer


def _search_pexels(api_key, query):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": 5, "orientation": "landscape"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        photo = photos[0]
        url = photo["src"]["large"]
        photographer = photo.get("photographer", "Pexels")
        return url, photographer
    except Exception as e:
        print(f"  WARNING: Pexels search failed for '{query}': {e}")
        return None
