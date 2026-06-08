import anthropic
import json
import os
import re
import time
from datetime import datetime
from image_fetcher import fetch_image

PERSONA_FILE    = os.path.join(os.path.dirname(__file__), "../config/persona.json")
AFFILIATES_FILE = os.path.join(os.path.dirname(__file__), "../config/affiliates.json")
KEYWORDS_FILE   = os.path.join(os.path.dirname(__file__), "keywords.json")
PROGRESS_FILE   = os.path.join(os.path.dirname(__file__), "progress.json")

MAX_RETRIES  = 3
RETRY_DELAY  = 10

# Keywords that signal a comparison/list article → triggers comparison table
COMPARISON_SIGNALS = {"best", "top", "vs", "versus", "compare", "comparison", "review", "reviews"}


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _is_comparison_keyword(keyword):
    words = set(keyword.lower().split())
    return bool(words & COMPARISON_SIGNALS)


def _get_internal_links(keyword, category):
    """Return up to 4 same-category completed article URLs, excluding the current keyword."""
    try:
        with open(KEYWORDS_FILE) as f:
            kw_data = json.load(f)
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
        completed = set(progress.get("completed", []))

        same_cat = [
            k["keyword"] for k in kw_data["keywords"]
            if k["keyword"] in completed
            and k["category"] == category
            and k["keyword"] != keyword
        ]
        return [f"/posts/{slugify(k)}/" for k in same_cat[:4]]
    except Exception:
        return []


def _normalize_content(content):
    """Strip code fences and normalize TOML front matter to YAML."""
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n", "", content)
        content = re.sub(r"\n```\s*$", "", content)
        content = content.strip()

    if content.startswith("+++"):
        content = content.replace("+++", "---", 2)
        parts = content.split("---", 2)
        if len(parts) == 3:
            fm = re.sub(r'^(\w+)\s*=\s*', r'\1: ', parts[1], flags=re.MULTILINE)
            content = "---" + fm + "---" + parts[2]

    content = re.sub(r'(---\n)```[a-zA-Z]*\n', r'\1', content)
    content = re.sub(r'\n```\s*$', '', content)
    return content


def _validate_content(content):
    """Raise ValueError if content doesn't have valid YAML front matter with required fields."""
    if not content.startswith("---\n"):
        raise ValueError("Content does not start with YAML front matter (---)")
    closing = content.find("\n---\n", 4)
    if closing == -1:
        raise ValueError("Front matter block is never closed")
    fm = content[4:closing]
    for field in ("title:", "date:", "draft:"):
        if field not in fm:
            raise ValueError(f"Front matter missing required field: {field}")


def write_article(keyword_entry):
    with open(PERSONA_FILE) as f:
        persona = json.load(f)
    with open(AFFILIATES_FILE) as f:
        affiliates = json.load(f)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    keyword  = keyword_entry["keyword"]
    category = keyword_entry["category"]

    is_comparison = _is_comparison_keyword(keyword)
    internal_links = _get_internal_links(keyword, category)

    # --- Build the structure-specific instructions ---
    if is_comparison:
        structure_instructions = """STRUCTURE (comparison/list article):
- After the opening 1-2 paragraphs, include a compact comparison table (4-6 rows, 3 columns max, e.g. Option | Best For | one key detail)
- Use H3 subheadings for each individual option (2-4 short paragraphs each)
- H2 for major sections only (e.g. "How to Choose", "FAQ")
- Maximum 4 H2 headings total"""
    else:
        structure_instructions = """STRUCTURE (informational article):
- Use H2 subheadings only
- Maximum 4 H2 headings total
- No tables required"""

    # --- Build internal links block ---
    if internal_links:
        links_block = "INTERNAL LINKS — include 1-2 of these naturally in the article body where relevant:\n" + \
                      "\n".join(f"- {url}" for url in internal_links)
    else:
        links_block = "INTERNAL LINKS — none available yet for this category; skip."

    prompt = f"""You are writing a blog article for DormRoomFinance.com as {persona['name']}, a {persona['age']}-year-old {persona['year']} at a {persona['school']}.

VOICE & STYLE:
{chr(10).join(f'- {s}' for s in persona['writing_style'])}

DISCLAIMER: "{persona['disclaimers']}"
AFFILIATE DISCLOSURE (include at top): "{affiliates['link_disclosure']}"

TOPIC: "{keyword}"
CATEGORY: {category}

{structure_instructions}

CONTENT REQUIREMENTS:
- Length: 1,100-1,400 words (tables count toward this; don't pad with prose)
- Hugo-compatible Markdown, YAML front matter with --- delimiters, NOT wrapped in code fences
- Front matter fields: title, date ({datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')}), description (150-160 chars, action-oriented — lead with the benefit, earn the click), categories (["{category}"]), tags (4-6 relevant tags), draft: false
- No horizontal rules between sections
- No hyphens or em dashes in article text
- One specific personal story or moment
- Where naturally relevant, mention real products or services (credit cards, apps, brokerages)
- End with "## Frequently Asked Questions" containing 4-5 Q&As. Format: **Q: question** followed by a 1-2 sentence answer. No "Bottom Line" section — let the last body section close naturally.

{links_block}

Write the complete article now, starting with the front matter."""

    last_error = None
    content = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            normalized = _normalize_content(raw)
            _validate_content(normalized)
            content = normalized
            break
        except Exception as e:
            last_error = e
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

    if content is None:
        raise RuntimeError(f"Article generation failed after {MAX_RETRIES} attempts: {last_error}")

    slug = slugify(keyword)

    print("  Fetching cover image...")
    image_path, photographer = fetch_image(keyword, slug, category)
    if image_path:
        cover_block = (
            f"cover:\n"
            f"  image: \"{image_path}\"\n"
            f"  alt: \"{keyword}\"\n"
            f"  caption: \"Photo by {photographer} on Pexels\"\n"
            f"  relative: false\n"
        )
        content = re.sub(
            r"(draft[: =]+false\n)",
            lambda m: m.group(1) + cover_block,
            content,
        )

    return content, slug, keyword, category
