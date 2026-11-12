import base64
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'automation'))
import article_writer as writer
import keyword_picker as picker
import main as pipeline
import auto_research as research
import auto_publisher as publisher

SOURCES=[{'url':'https://www.consumerfinance.gov/test','title':'A'},{'url':'https://www.irs.gov/test','title':'B'}]
def article():
 return {'title':'Practical student budget','description':'Plan a month of spending.','body':'## Start here\n\n'+'Useful educational guidance for a student budget. '*65+'\n\n[Source A]('+SOURCES[0]['url']+') and [Source B]('+SOURCES[1]['url']+').'}
class Response:
 def __init__(self,status,data):self.status_code=status;self.data=data
 def json(self):return self.data
 def raise_for_status(self):
  if self.status_code>=400:raise RuntimeError('HTTP '+str(self.status_code))

class AutoTests(unittest.TestCase):
 def test_valid_article(self):writer.validate_article(article(),SOURCES)
 def test_rejects_unverified_stories(self):
  a=article();a['body']+=' My real bank account did this.'
  with self.assertRaises(ValueError):writer.validate_article(a,SOURCES)
 def test_rejects_unknown_links(self):
  for link in ['https://example.com/fake','/posts/not-real/']:
   a=article();a['body']+=' [Read]('+link+')'
   with self.assertRaises(ValueError):writer.validate_article(a,SOURCES)
 def test_rejects_bad_shape(self):
  for body in ['short','# Duplicate title\n'+article()['body'],article()['body']+'<script>x</script>']:
   a=article();a['body']=body
   with self.assertRaises(ValueError):writer.validate_article(a,SOURCES)
 def test_primary_domains(self):
  self.assertTrue(research.allowed_url('https://www.irs.gov/retirement'))
  for url in ['http://irs.gov','https://irs.gov.evil.com','https://user:pass@irs.gov/','https://localhost/']:
   self.assertFalse(research.allowed_url(url))
 def test_research_rejects_no_live_results(self):
  response=NS(stop_reason='end_turn',content=[NS(type='text',text='A claim.',citations=[])])
  api=NS(messages=NS(create=lambda **kwargs:response))
  with patch.object(research,'client',return_value=api),self.assertRaises(ValueError):research._research_with_search('budget')
 def test_research_uses_live_citations(self):
  cites=[NS(url=x['url'],title=x['title'],cited_text='A supported fact') for x in SOURCES]
  response=NS(stop_reason='end_turn',content=[NS(type='web_search_tool_result',content=[NS(type='web_search_result')]),NS(type='text',text='Supported notes.',citations=cites)])
  api=NS(messages=NS(create=lambda **kwargs:response))
  with patch.object(research,'client',return_value=api):self.assertEqual(len(research._research_with_search('budget')['sources']),2)
 def test_picker_needs_no_review_pack(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'content/posts').mkdir(parents=True)
   keys=root/'keys.json';progress=root/'progress.json'
   keys.write_text(json.dumps({'keywords':[{'keyword':'new budget topic','category':'Budgeting'}]}));progress.write_text(json.dumps({'completed':[],'total_articles':100}))
   with patch.object(picker,'ROOT',root),patch.object(picker,'KEYWORDS_FILE',str(keys)),patch.object(picker,'PROGRESS_FILE',str(progress)):
    self.assertEqual(picker.pick_next_keyword()[0]['keyword'],'new budget topic')
 def test_idempotent_progress(self):
  with tempfile.TemporaryDirectory() as tmp:
   progress={'completed':[],'total_articles':100}
   with patch.object(picker,'PROGRESS_FILE',str(Path(tmp)/'progress.json')):
    picker.mark_keyword_complete({'keyword':'topic'},progress);picker.mark_keyword_complete({'keyword':'topic'},progress)
   self.assertEqual(progress['total_articles'],101)
 def test_daily_guard(self):
  with patch.object(pipeline,'already_ran_today',return_value=True),patch.object(writer,'write_article') as generate,patch.object(publisher,'publish_article') as publish:
   pipeline.main();generate.assert_not_called();publish.assert_not_called()
 def test_saved_article_recovery(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'automation').mkdir();pending=root/'automation/pending.json';state=root/'automation/run.json';progress=root/'automation/progress.json'
   pending.write_text(json.dumps({'entry':{'keyword':'topic','category':'Budgeting'},'slug':'topic','content':'Exact saved article'}));progress.write_text(json.dumps({'completed':[],'total_articles':100}))
   fake_date=NS(today=lambda:NS(weekday=lambda:3,isoformat=lambda:'2026-11-12'))
   with patch.object(pipeline,'ROOT',root),patch.object(pipeline,'PENDING_FILE',pending),patch.object(pipeline,'LAST_RUN_FILE',state),patch.object(pipeline,'date',fake_date),patch.object(picker,'PROGRESS_FILE',str(progress)),patch.dict('os.environ',{'ANTHROPIC_API_KEY':'test','GITHUB_TOKEN':'test','GITHUB_USERNAME':'test','GITHUB_REPO':'test'},clear=True),patch.object(writer,'write_article') as generate,patch.object(publisher,'publish_article',return_value=(True,'https://example.com',False)) as publish:
    pipeline.main();generate.assert_not_called();publish.assert_called_once_with('Exact saved article','topic')
    self.assertFalse(pending.exists());self.assertEqual(json.loads(progress.read_text())['total_articles'],101)
 def test_failure_keeps_pending(self):
  with tempfile.TemporaryDirectory() as tmp:
   pending=Path(tmp)/'pending.json';pending.write_text(json.dumps({'entry':{'keyword':'topic'},'slug':'topic','content':'saved'}))
   fake_date=NS(today=lambda:NS(weekday=lambda:3,isoformat=lambda:'2026-11-12'))
   with patch.object(pipeline,'PENDING_FILE',pending),patch.object(pipeline,'already_ran_today',return_value=False),patch.object(pipeline,'date',fake_date),patch.dict('os.environ',{'ANTHROPIC_API_KEY':'test','GITHUB_TOKEN':'test','GITHUB_USERNAME':'test','GITHUB_REPO':'test'},clear=True),patch.object(publisher,'publish_article',side_effect=RuntimeError('network failed')):
    with self.assertRaises(RuntimeError):pipeline.main()
   self.assertTrue(pending.exists())
 def test_publisher_refuses_overwrite(self):
  class Session:
   headers={}
   def request(self,method,url,**kwargs):
    if url.endswith('/git/ref/heads/main'):return Response(200,{'object':{'sha':'head'}})
    return Response(200,{'content':base64.b64encode(b'existing different article').decode()})
  with patch.dict('os.environ',{'GITHUB_USERNAME':'test','GITHUB_REPO':'test','GITHUB_TOKEN':'test'}),patch.object(publisher.requests,'Session',return_value=Session()):
   with self.assertRaises(RuntimeError):publisher.publish_article('new content','topic')
 def test_publish_retry_recovers_same_content(self):
  class Session:
   headers={}
   def request(self,method,url,**kwargs):
    if url.endswith('/git/ref/heads/main'):return Response(200,{'object':{'sha':'head'}})
    return Response(200,{'content':base64.b64encode(b'exact same content').decode()})
  with patch.dict('os.environ',{'GITHUB_USERNAME':'test','GITHUB_REPO':'test','GITHUB_TOKEN':'test'}),patch.object(publisher.requests,'Session',return_value=Session()):
   self.assertTrue(publisher.publish_article('exact same content','topic')[0])

class PublicationTests(unittest.TestCase):
 def test_new_article_is_atomic_and_fast_forward_only(self):
  calls=[]
  class Session:
   headers={}
   def request(self,method,url,**kwargs):
    calls.append((method,url,kwargs))
    if url.endswith('/git/ref/heads/main'):return Response(200,{'object':{'sha':'head'}})
    if '/contents/' in url:return Response(404,{})
    if url.endswith('/git/commits/head'):return Response(200,{'tree':{'sha':'base-tree'}})
    if url.endswith('/git/trees'):return Response(201,{'sha':'new-tree'})
    if url.endswith('/git/commits'):return Response(201,{'sha':'new-commit'})
    if url.endswith('/git/refs/heads/main'):return Response(200,{})
    raise AssertionError(url)
  with patch.dict('os.environ',{'GITHUB_USERNAME':'test','GITHUB_REPO':'test','GITHUB_TOKEN':'test'}),patch.object(publisher.requests,'Session',return_value=Session()):
   self.assertTrue(publisher.publish_article('article','auto-publisher-unit-test')[0])
  trees=[x for x in calls if x[1].endswith('/git/trees')]
  self.assertEqual(len(trees),1);self.assertEqual(trees[0][2]['json']['base_tree'],'base-tree')
  updates=[x for x in calls if x[0]=='PATCH'];self.assertEqual(updates[0][2]['json'],{'sha':'new-commit','force':False})
 def test_off_schedule_never_generates(self):
  with patch.object(pipeline,'already_ran_today',return_value=False),patch.object(pipeline,'date',NS(today=lambda:NS(weekday=lambda:0))),patch.object(writer,'write_article') as generate:
   pipeline.main();generate.assert_not_called()
 def test_primary_fetch_fallback(self):
  response=NS(url='https://consumer.gov/your-money/making-budget',text='<html><main>'+('Official budgeting information. '*100)+'</main><script>ignore this</script></html>',raise_for_status=lambda:None)
  import requests
  with patch.object(requests,'get',return_value=response):
   data=research._fetch_primary_sources('student budget')
  self.assertEqual(len(data['sources']),2);self.assertNotIn('ignore this',data['notes'])

if __name__=='__main__':unittest.main()
