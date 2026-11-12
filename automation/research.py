"""Validate source notes supplied by an editor before drafting. No automatic approval."""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


def load_research(path, keyword, today=None):
    data = json.loads(Path(path).read_text())
    today = today or date.today()
    if data.get('keyword') != keyword:
        raise ValueError('Research keyword must match the requested topic')
    if not isinstance(data.get('reviewed_by'), str) or not data['reviewed_by'].strip():
        raise ValueError('An editor must identify who checked the source notes')
    sources = data.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('At least one checked source is required')
    for source in sources:
        url = urlparse(source.get('url', ''))
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Sources must have public HTTPS URLs without credentials')
        checked = date.fromisoformat(source.get('verified_on', ''))
        if not 0 <= (today - checked).days <= 14:
            raise ValueError('Recheck source notes older than 14 days or dated in the future')
        claims = source.get('claims')
        if not isinstance(claims, list) or not claims or any(not isinstance(x, str) or not x.strip() for x in claims):
            raise ValueError('Each source needs specific checked claims')
    return data
