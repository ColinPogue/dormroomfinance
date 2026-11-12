import json
import os
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
KEYWORDS_FILE=str(ROOT/'automation/keywords.json')
PROGRESS_FILE=str(ROOT/'automation/progress.json')


def pick_next_keyword():
    from article_writer import slugify
    keywords=json.loads(Path(KEYWORDS_FILE).read_text())['keywords']
    progress=json.loads(Path(PROGRESS_FILE).read_text())
    completed=set(progress.get('completed',[]))
    remaining=[k for k in keywords if k['keyword'] not in completed and not (ROOT/'content/posts'/(slugify(k['keyword'])+'.md')).exists()]
    if not remaining:
        from article_writer import parse_json,response_text
        from auto_research import client,MODEL
        prompt='''Propose 12 distinct, useful evergreen US college-student money topics.
Avoid product rankings, live rates, legal changes, forecasts and near-duplicates of existing topics.
Return JSON {"keywords":[{"keyword":"specific topic","category":"one category"}]}.
Categories: Budgeting, Saving Money, First Job Finances, Credit Cards, Investing, Student Loans, Banking, Side Hustles.
Existing topics: '''+json.dumps([x['keyword'] for x in keywords])
        data=parse_json(response_text(client().messages.create(model=MODEL,max_tokens=2000,messages=[{'role':'user','content':prompt}])))
        categories={x['category'] for x in keywords};known={slugify(x['keyword']) for x in keywords}
        for item in data.get('keywords',[]):
            if not isinstance(item,dict) or not isinstance(item.get('keyword'),str) or item.get('category') not in categories:continue
            slug=slugify(item['keyword'])
            if not slug or slug in known:continue
            known.add(slug);keywords.append(item);remaining.append(item)
        if remaining:
            tmp=Path(KEYWORDS_FILE+'.tmp');tmp.write_text(json.dumps({'keywords':keywords},indent=2)+'\n');os.replace(str(tmp),KEYWORDS_FILE)
    return (random.choice(remaining) if remaining else None),progress


def mark_keyword_complete(keyword_entry,progress):
    if keyword_entry['keyword'] not in progress.setdefault('completed',[]):
        progress['completed'].append(keyword_entry['keyword']);progress['total_articles']=progress.get('total_articles',0)+1
        tmp=Path(PROGRESS_FILE+'.tmp');tmp.write_text(json.dumps(progress,indent=2)+'\n');os.replace(str(tmp),PROGRESS_FILE)
