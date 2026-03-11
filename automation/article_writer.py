import anthropic
import json
import os
import re
from datetime import datetime

PERSONA_FILE = os.path.join(os.path.dirname(__file__), "../config/persona.json")
AFFILIATES_FILE = os.path.join(os.path.dirname(__file__), "../config/affiliates.json")


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
- Include a Hugo front matter block at the very top with: title, date ({datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')}), description (SEO meta description, 150-160 chars), categories (["{category}"], tags (3-5 relevant tags), draft: false
- H2 and H3 subheadings throughout
- At least one personal anecdote or relatable student moment
- Actionable takeaways
- Where naturally relevant, mention real products/services (credit cards, apps, brokerages) — these will be affiliate links
- End with a clear "Bottom Line" or "TL;DR" section
- Internal link placeholders like [related article](/posts/related-slug/) where relevant

Write the complete article now, starting with the front matter.
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )

    content = message.content[0].text
    slug = slugify(keyword)
    return content, slug, keyword, category
