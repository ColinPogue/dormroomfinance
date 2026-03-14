import anthropic
import json
import os
import re
import time
from datetime import datetime
from image_fetcher import fetch_image

PERSONA_FILE = os.path.join(os.path.dirname(__file__), "../config/persona.json")
AFFILIATES_FILE = os.path.join(os.path.dirname(__file__), "../config/affiliates.json")

MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds between retries


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def write_article(keyword_entry):
    with open(PERSONA_FILE) as f:
        persona = json.load(f)

    with open(AFFILIATES_FILE) as f:
        affiliates = json.load(f)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    keyword = keyword_entry["keyword"]
    category = keyword_entry["category"]

    prompt = f"""You are writing a blog article for DormRoomFinance.com as {persona['name']}, a {persona['age']}-year-old {persona['year']} at a {persona['school']}.

VOICE & STYLE:
{chr(10).join(f'- {s}' for s in persona['writing_style'])}

DISCLAIMER TO INCLUDE: "{persona['disclaimers']}"

AFFILIATE DISCLOSURE TO INCLUDE AT TOP: "{affiliates['link_disclosure']}"

TOPIC/KEYWORD TO TARGET: "{keyword}"
CATEGORY: {category}

REQUIREMENTS:
- Length: 1,200-1,500 words
- Format: Hugo-compatible Markdown
- Include a Hugo front matter block at the very top with: title, date ({datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')}), description (SEO meta description, 150-160 chars), categories (["{category}"]), tags (3-5 relevant tags), draft: false
- Use H2 subheadings only (no H3). Maximum 4 subheadings in the whole article
- Do NOT put a horizontal rule (---) between every section. Use them sparingly or not at all
- No hyphens or em dashes anywhere in the article text. Rewrite any sentence that would need one
- At least one specific personal story or moment
- Where naturally relevant, mention real products/services (credit cards, apps, brokerages) — these will be affiliate links
- End with a short "Bottom Line" section that is 2-3 sentences max, not a bulleted list
- After the Bottom Line, add a "## Frequently Asked Questions" section with 3 short Q&As. Format each as "**Q: [question]**" followed by a 2-3 sentence answer

Write the complete article now, starting with the front matter.
"""

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            content = message.content[0].text.strip()
            # Strip markdown code fences if Claude wraps the output
            if content.startswith("```"):
                content = re.sub(r"^```[a-z]*\n", "", content)
                content = re.sub(r"\n```$", "", content)
            slug = slugify(keyword)

            # Fetch cover image from Pexels and inject into frontmatter
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
                    r"(draft: false\n)",
                    r"\1" + cover_block,
                    content
                )

            return content, slug, keyword, category

        except Exception as e:
            last_error = e
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

    raise RuntimeError(f"Claude API failed after {MAX_RETRIES} attempts: {last_error}")
