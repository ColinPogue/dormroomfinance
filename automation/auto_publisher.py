"""Commit an article and optional image atomically; never overwrite an existing article."""
import base64
import os
from pathlib import Path
import requests


def publish_article(content,slug):
    owner=os.environ['GITHUB_USERNAME'];repo=os.environ['GITHUB_REPO']
    base=f'https://api.github.com/repos/{owner}/{repo}'
    session=requests.Session();session.headers.update({'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json'})
    def call(method,path,**kwargs):
        response=session.request(method,base+path,timeout=30,**kwargs)
        return response
    branch=call('GET','/git/ref/heads/main');branch.raise_for_status();head=branch.json()['object']['sha']
    path='content/posts/'+slug+'.md'
    existing=call('GET','/contents/'+path,params={'ref':head})
    if existing.status_code==200:
        text=base64.b64decode(existing.json()['content']).decode('utf-8')
        if text==content:return True,'https://dormroomfinance.com/posts/'+slug+'/',False
        raise RuntimeError('Article URL already exists with different content; refusing to overwrite')
    if existing.status_code!=404:existing.raise_for_status()
    commit=call('GET','/git/commits/'+head);commit.raise_for_status()
    elements=[{'path':path,'mode':'100644','type':'blob','content':content}]
    image=Path(__file__).resolve().parent.parent/'static/images/posts'/(slug+'.jpg')
    if image.exists():
        blob=call('POST','/git/blobs',json={'content':base64.b64encode(image.read_bytes()).decode('ascii'),'encoding':'base64'});blob.raise_for_status()
        elements.append({'path':'static/images/posts/'+slug+'.jpg','mode':'100644','type':'blob','sha':blob.json()['sha']})
    tree=call('POST','/git/trees',json={'base_tree':commit.json()['tree']['sha'],'tree':elements});tree.raise_for_status()
    new=call('POST','/git/commits',json={'message':'Add sourced automated article: '+slug,'tree':tree.json()['sha'],'parents':[head]});new.raise_for_status()
    update=call('PATCH','/git/refs/heads/main',json={'sha':new.json()['sha'],'force':False})
    if update.status_code not in (200,201):raise RuntimeError('GitHub refused the branch update; no force, reset, or automatic rebase attempted')
    return True,'https://dormroomfinance.com/posts/'+slug+'/',image.exists()
