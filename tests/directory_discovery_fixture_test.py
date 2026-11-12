"""Prove curated-directory discovery is review-only and resilient to missing sites."""
from __future__ import annotations
import sys,json, pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import directory_discovery as d
import registry_audit as a
source={'id':'cambridge','name':'Cambridge recruiting doctors','url':'https://www.doctors4cambridge.com/contact.htm','mode':'table'}
html='''<html><body><table><tr><td>Dr. Amara Test</td><td>New Family Medical Centre</td><td>100 Main Street, Cambridge</td></tr></table></body></html>'''
rows=d.parse_candidates(html,source)
assert d.parse_candidates('<table><tr><td>Walk In Clinic</td><td>Address</td><td>Telephone</td></tr></table>',source)==[]
assert len(rows)==1 and rows[0]['title']=='Dr. Amara Test',rows
page_source={'id':'woodstock_news','name':'Woodstock news','url':'https://www.cityofwoodstock.ca/news/','mode':'news'}
news='''<a href="/news/posts/new-family-physician-opens/">New family physician opens clinic in Woodstock</a><a href="/news/posts/pool-closed/">Pool closure announced</a>'''
assert len(d.parse_candidates(news,page_source))==1
brant={'id':'brant_hospital','name':'Brant BCHS','url':'https://www.bchsys.org/patients-and-visitors/finding-a-doctor/','mode':'people'}
brant_html='<p>Dr. Clara Obanor</p><p>Bonavista Medical Center</p><p>Health811</p>'
assert len(d.parse_candidates(brant_html,brant))==2
state={'sources':{}};queue={'items':[]};clinics=[{'id':'c1','name':'Existing Clinic','providers':'Dr. Existing','community':'Cambridge'}]
sources=[source]
res=d.process(sources,{'cambridge':html},state,queue,clinics,'2026-11-11')
assert res['baselines']==1 and res['new_directory_leads']==1,res
assert queue['items'][0]['intake_status']=='unconfirmed'
assert queue['items'][0]['review_status']=='pending'
assert queue['items'][0]['radius_checked'] is False
res=d.process(sources,{'cambridge':html},state,queue,clinics,'2026-11-12')
assert res['new_directory_leads']==0 and len(queue['items'])==1
changed_text=html.replace('New Family Medical Centre','New Family Medical Centre now has waitlist')
res=d.process(sources,{'cambridge':changed_text},state,queue,clinics,'2026-11-12')
assert res['new_directory_leads']==1 and len(queue['items'])==2
res=d.process(sources,{'cambridge':None},state,queue,clinics,'2026-11-13')
assert res['failed']==1 and len(queue['items'])==2
# A changed directory doesn't imply closed intake.
changed='<html><body><table><tr><td>Dr. Other Test</td><td>Family Medical Centre</td></tr></table></body></html>'
res=d.process(sources,{'cambridge':changed},state,queue,clinics,'2026-11-14')
assert res['new_directory_leads']==1 and res['listing_removals_to_review']==1
assert all(x['intake_status']=='unconfirmed' for x in queue['items'])
assert all('clinic' not in x.get('new_status','') for x in queue['items'])
# Professional register audit is manual only, and deduplicated within a week.
s={'last_week':None};q={'items':[]}
assert a.prepare(s,q,'2026-11-16')==1
assert a.prepare(s,q,'2026-11-16')==0
assert a.prepare(s,q,'2026-11-17')==0
assert q['items'][0]['intake_status']=='not provided by registries'
print('PASS: directory discovery queues only review items; no auto acceptance/closures; audits are manual and bounded')
