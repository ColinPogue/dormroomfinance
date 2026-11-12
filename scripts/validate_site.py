"""Check generated HTML, preserved URLs, metadata, and internal navigation without a browser."""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.links=[];self.ids=set();self.h1=0;self.canon=[];self.noindex=False;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if a.get('id'):self.ids.add(a['id'])
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag in ('script','img') and a.get('src'):self.links.append(a['src'])
        if tag=='link' and a.get('rel')=='canonical':self.canon.append(a.get('href'))
        if tag=='meta' and a.get('name')=='robots' and 'noindex' in a.get('content',''):self.noindex=True

def target(path):
    f=PUBLIC/unquote(path).lstrip('/')
    if f.is_dir():f=f/'index.html'
    return f

errors=[];broken={};pages={};checked=0
for f in PUBLIC.rglob('*.html'):
    text=f.read_text(); rel=f.relative_to(PUBLIC)
    # Hugo aliases intentionally contain only redirects.
    if 'http-equiv=refresh' in text or 'http-equiv="refresh"' in text:continue
    page=Page(text);pages[f]=page;checked+=1
    if f.name not in ('404.html',) and not f.name.startswith('google') and page.h1!=1:errors.append(f'{rel}: {page.h1} h1 headings')
    if f.name!='404.html' and not f.name.startswith('google') and len(page.canon)!=1:errors.append(f'{rel}: expected one canonical URL')
    for link in page.links:
        url=urlsplit(link)
        if url.scheme and url.scheme not in ('http','https'):continue
        if url.netloc and url.netloc!='dormroomfinance.com':continue
        if not url.path:continue
        resolved=target(url.path) if url.path.startswith('/') else target('/'+str(rel.parent/url.path))
        if not resolved.exists():broken.setdefault(link,[]).append(str(rel))
# All 100 original article paths must remain public and self-canonical.
audit=json.loads((ROOT/'docs/content-audit.json').read_text())
for row in audit:
    slug=row['slug']; f=PUBLIC/'posts'/slug/'index.html'
    if f not in pages:errors.append(f'Missing original article: {slug}');continue
    pg=pages[f]
    if pg.noindex:errors.append(f'Article unexpectedly noindexed: {slug}')
    if pg.canon != ['https://dormroomfinance.com/posts/'+slug+'/']:errors.append(f'Wrong canonical: {slug}')
for path in ['index.html','sitemap.xml','robots.txt','index.json','tools/student-budget/index.html','tools/internship-budget.csv','foodtalk-privacy/index.html']:
    if not (PUBLIC/path).exists():errors.append('Missing '+path)
for link,refs in broken.items():errors.append(f'Broken internal link: {link} ({len(refs)} pages; {refs[0]})')
print(f'Checked {checked} rendered HTML pages and all {len(audit)} original article URLs.')
for error in errors: print(error)
print(f'{len(errors)} validation errors.')
sys.exit(bool(errors))
