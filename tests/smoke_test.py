import os
import sys,pathlib,re,json,threading,http.server,functools
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
site=ROOT/'site'/'index.html'
ARTIFACTS=ROOT/'test-results'
ARTIFACTS.mkdir(exist_ok=True)
s=site.read_text()
assert 'connect-src \'none\'' in s
assert 'No patient-address search' in s
assert 'https://cdn' not in s
records=json.loads((ROOT/'data/clinics.json').read_text())['clinics'];N=len(records)
N_ONGOING=sum(c.get('care_model') in ('ongoing','both') for c in records)
from datetime import date
sys.path.insert(0,str(ROOT/'scripts'))
from common import effective_status
expected_accepting=sum(effective_status(c,date.today())=='accepting' for c in records)
expected_reported=sum(effective_status(c,date.today())=='reported' for c in records)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'site')))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=site.as_uri()
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1365,'height':900},device_scale_factor=1)
 blocked=[]; errors=[]
 page.on('request',lambda req:blocked.append(req.url) if req.url.startswith('http') and '127.0.0.1' not in req.url else None)
 page.on('pageerror',lambda err:errors.append(str(err)))
 page.goto(url);page.wait_for_selector('.item')
 print('INITIAL',page.locator('#count').inner_text());assert page.locator('.item').count()==N_ONGOING
 page.select_option('#care','all');assert page.locator('.item').count()==N
 page.select_option('#status','accepting');assert page.locator('.item').count()==expected_accepting
 page.select_option('#status','reported');assert page.locator('.item').count()==expected_reported
 page.select_option('#status','all');page.locator('#search').fill('Oxfordia')
 assert page.locator('.item').count()==1 and 'Oxfordia' in page.locator('.item').first.inner_text()
 page.locator('#reset').click(); assert page.locator('.item').count()==N_ONGOING
 assert page.locator('#care').input_value()=='ongoing'
 page.select_option('#care','all');assert page.locator('.item').count()==N
 page.select_option('#town','Tillsonburg');assert page.locator('.item').count()==5
 assert page.locator('.town-group').count()==1, 'Town filter must also filter map'
 page.select_option('#town','all')
 assert page.locator('.town-group').count()==len({c['community'] for c in records})
 assert not page.locator('input[placeholder*="address"]').count()
 assert 'No patient-address search' in page.locator('.notice').inner_text()
 assert not errors,errors
 assert not blocked,blocked
 page.select_option('#town','all');page.screenshot(path=str(ARTIFACTS/'desktop.png'),full_page=True)
 print('PASS: dynamic clinic dataset, filters, Oxfordia name search, map markers, no HTTP requests, no JS errors')
 mob=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
 mob.goto(url);mob.wait_for_selector('.item');print('MOBILE',mob.locator('.item').count())
 assert mob.locator('.item').count()==N_ONGOING
 mob.select_option('#care','all');assert mob.locator('.item').count()==N
 assert mob.evaluate('document.documentElement.scrollWidth <= window.innerWidth+3'),'horizontal page overflow'
 mob.screenshot(path=str(ARTIFACTS/'mobile.png'),full_page=False)
 browser.close()
server.shutdown()
