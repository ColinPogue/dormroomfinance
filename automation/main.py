#!/usr/bin/env python3
"""Scheduled research-backed drafting. Never publishes or marks an article complete."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')


def main():
    from keyword_picker import pick_next_keyword
    from article_writer import write_article
    entry, _ = pick_next_keyword()
    if entry is None:
        print('No new topic has fresh checked source notes. Nothing generated or published.')
        return
    if not os.environ.get('ANTHROPIC_API_KEY'):
        raise RuntimeError('ANTHROPIC_API_KEY is required for drafting')
    content, slug, _, _ = write_article(entry)
    directory = ROOT / 'editorial-drafts'
    directory.mkdir(exist_ok=True)
    path = directory / (slug + '.md')
    # Exclusive creation protects an existing draft even if two scheduler runs overlap.
    with path.open('x') as output:
        output.write(content)
    print('Draft saved for editorial review: ' + str(path))
    print('No GitHub publication, notification, or completed-keyword update occurred.')


if __name__ == '__main__':
    main()
