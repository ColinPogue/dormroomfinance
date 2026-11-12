"""Check the actual custom-domain release after GitHub Pages deployment."""
import time
from urllib.request import Request, urlopen

checks={
 '/':'Big plans.',
 '/start-here/':'A better start with money',
 '/tools/student-budget/':'budget-form',
 '/posts/best-credit-card-for-college-students-with-no-credit-history/':'Source notes included.',
 '/search/':'searchStatus',
 '/robots.txt':'Sitemap: https://dormroomfinance.com/sitemap.xml',
 '/sitemap.xml':'https://dormroomfinance.com/',
 '/tools/budget.js':'monthlyIrregular',
}
last=None
for attempt in range(12):
 try:
  for path,expected in checks.items():
   request=Request('https://dormroomfinance.com'+path+'?release=20261112',headers={'User-Agent':'DormRoomFinance-Release-Check/1.0','Cache-Control':'no-cache'})
   with urlopen(request,timeout=20) as response:
    assert response.status==200,(path,response.status)
    content=response.read().decode('utf-8')
   assert expected in content,(path,'expected release content missing')
   if path.endswith('/'):
    assert '2026-11-12-makeover-v1' in content,(path,'release marker missing')
  print('Live custom-domain checks passed: all 8 URLs returned HTTP 200 with expected content.')
  break
 except Exception as error:
  last=error
  print('Release check not ready:',str(error))
  if attempt==11:raise
  time.sleep(5)
