#!/usr/bin/env python3
"""Hands-off Tue/Thu/Sat publishing with live research and automatic content checks."""
import argparse
import fcntl
import json
import os
import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parent.parent
load_dotenv(ROOT/'.env')
LAST_RUN_FILE=ROOT/'automation/last_run.json'
PENDING_FILE=ROOT/'automation/pending_article.json'


def atomic_json(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(str(tmp),str(path))


def already_ran_today():
    if not LAST_RUN_FILE.exists():return False
    # Fail visibly on corrupt state rather than accidentally producing duplicates.
    return json.loads(LAST_RUN_FILE.read_text()).get('last_run_date')==date.today().isoformat()


def main(dry_run=False):
    from article_writer import write_article
    from keyword_picker import pick_next_keyword,mark_keyword_complete,PROGRESS_FILE
    from auto_publisher import publish_article
    if not dry_run and already_ran_today():
        print('Already published today; skipping.');return
    if not dry_run and date.today().weekday() not in (1,3,5):
        print('Publishing runs Tuesday, Thursday and Saturday; skipping.');return
    required=['ANTHROPIC_API_KEY']+([] if dry_run else ['GITHUB_TOKEN','GITHUB_USERNAME','GITHUB_REPO'])
    missing=[name for name in required if not os.environ.get(name)]
    if missing:raise RuntimeError('Missing configuration: '+', '.join(missing))
    if PENDING_FILE.exists() and not dry_run:
        pending=json.loads(PENDING_FILE.read_text())
        print('Resuming the saved article without generating a duplicate.')
    else:
        pending=None;failures=[];tried=set()
        for attempt in range(3):
            entry,_=pick_next_keyword()
            if entry is None:raise RuntimeError('Automatic topic expansion returned no new topic')
            if entry['keyword'] in tried:continue
            tried.add(entry['keyword'])
            try:
                content,slug,keyword,category=write_article(entry)
                pending={'entry':entry,'content':content,'slug':slug,'created_on':date.today().isoformat()}
                break
            except Exception as error:
                failures.append(type(error).__name__)
                print('Automated research/content check failed; trying another topic ('+type(error).__name__+').')
        if pending is None:raise RuntimeError('No article passed automated checks: '+', '.join(failures))
        if dry_run:
            folder=ROOT/'exports/automatic-validation';folder.mkdir(parents=True,exist_ok=True)
            (folder/(pending['slug']+'.md')).write_text(pending['content'])
            print('Live generation checks passed. Validation copy saved; no GitHub write or email sent.');return
        atomic_json(PENDING_FILE,pending)
    # Use the exact saved article on retry, including after an ambiguous network timeout.
    success,url,_=publish_article(pending['content'],pending['slug'])
    if not success:raise RuntimeError('Publication failed')
    progress=json.loads(Path(PROGRESS_FILE).read_text())
    mark_keyword_complete(pending['entry'],progress)
    # Keep a local copy so the next run can link to and deduplicate the new article.
    local=ROOT/'content/posts'/(pending['slug']+'.md');local.parent.mkdir(parents=True,exist_ok=True);local.write_text(pending['content'])
    atomic_json(LAST_RUN_FILE,{'last_run_date':date.today().isoformat()})
    PENDING_FILE.unlink()
    print('Article committed: '+url+' (GitHub Pages validates and deploys automatically).')
    # The existing email is informational, never an approval request.
    if all(os.environ.get(k) for k in ['GMAIL_ADDRESS','GMAIL_APP_PASSWORD','NOTIFICATION_EMAIL']):
        from notifier import send_notification
        try:send_notification(pending['entry']['keyword'],pending['entry']['category'],url,progress['total_articles'])
        except Exception:print('Informational notification unavailable; article already committed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
    with (ROOT/'automation/.publish.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another publishing run is active; skipping.');sys.exit(0)
        try:main(dry_run=args.dry_run)
        except Exception as error:
            print('Automatic publishing failed: '+type(error).__name__+'. No review is required; check the automation logs for the failed stage.')
            raise
