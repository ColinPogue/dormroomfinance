import json
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYWORDS_FILE = str(ROOT / 'automation/keywords.json')
PROGRESS_FILE = str(ROOT / 'automation/progress.json')


def pick_next_keyword():
    from article_writer import slugify
    from research import load_research
    keywords = json.loads(Path(KEYWORDS_FILE).read_text())['keywords']
    progress = json.loads(Path(PROGRESS_FILE).read_text())
    completed = set(progress.get('completed', []))
    remaining = []
    for item in keywords:
        slug = slugify(item['keyword'])
        # Never cycle through old keywords or overwrite reviewed/published content.
        if item['keyword'] in completed or (ROOT / 'content/posts' / (slug + '.md')).exists() or (ROOT / 'editorial-drafts' / (slug + '.md')).exists():
            continue
        path = ROOT / 'research' / (slug + '.json')
        if not path.exists():
            continue
        try:
            load_research(path, item['keyword'])
        except (ValueError, KeyError, TypeError, OSError):
            continue
        remaining.append(item)
    if not remaining:
        return None, progress
    return random.choice(remaining), progress


def mark_keyword_complete(keyword_entry, progress):
    """Only use after a separate validated public release; drafting never calls this."""
    if keyword_entry['keyword'] not in progress.setdefault('completed', []):
        progress['completed'].append(keyword_entry['keyword'])
        progress['total_articles'] = progress.get('total_articles', 0) + 1
        tmp = Path(PROGRESS_FILE + '.tmp')
        tmp.write_text(json.dumps(progress, indent=2) + '\n')
        os.replace(str(tmp), PROGRESS_FILE)
