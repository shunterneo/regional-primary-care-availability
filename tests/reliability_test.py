"""Offline reliability: evidence clocks, blocked pages, and monitoring failures."""
import sys,pathlib,datetime as dt,copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from monitor_health import assess
from check_sources import usable_page
from evidence_policy import display_intake_status,display_expiry
assert not usable_page('<html><h1>Just a moment</h1><p>Verify that you are human to continue to the clinic</p></html>')
assert not usable_page('<html></html>')
assert usable_page('<h1>New patients</h1><p>Our family practice is accepting new patients. Please call reception.</p>')
now=dt.datetime(2026,11,12,tzinfo=dt.timezone.utc)
db={'clinics':[{'evidence_url':'https://clinic.test'}]}
s={'last_run':now.isoformat(),'sources':{'https://clinic.test':{'last_error':None,'last_success':now.isoformat()}}}
assert assess(db,s,now)['healthy']
assert not assess(db,s,now+dt.timedelta(hours=37))['healthy']
s['sources']['https://clinic.test']['last_error']='HTTP 403'
assert assess(db,s,now)['failed_count']==1
assert assess(db,{'sources':{}},now)['unscanned_count']==1
c={'status':'waitlist','last_reviewed':'2026-11-12','intake_reviewed_on':'2026-09-01'}
assert display_intake_status(c,now.date())=='needs_review','address edits must not renew old intake'
c={'status':'accepting','care_model':'ongoing','clinic_url':'https://clinic.test','evidence_url':'https://clinic.test/intake','intake_verification':{'tier':'clinic_first_party','scope':'location','method':'public_webpage_review','source_url':'https://clinic.test/intake','reviewed_on':'2026-11-01','finding':'Family practice accepts new patients'}}
assert display_expiry(c,now.date())=='2026-11-23'
assert display_intake_status(c,dt.date(2026,11,22))=='accepting'
assert display_intake_status(c,dt.date(2026,11,23))=='needs_review'
print('PASS: monitoring health, challenge rejection, field freshness and exclusive expiry')
from apply_site_edit import apply_edit
fixture={'id':'test','name':'Clinic Test','community':'Tillsonburg','address':'1 Public Road','care_model':'ongoing','status':'waitlist','last_reviewed':'2026-09-01','phone':'123','intake_detail':'A published waitlist','evidence_url':'https://clinic.test','clinic_url':'https://clinic.test'}
updated,event=apply_edit({'clinics':[fixture]}, {'version':1,'clinic_id':'test','base_reviewed':'2026-09-01','changes':{'phone':'456'},'base':{'phone':'123'},'source_url':'https://clinic.test','review_note':'Verified only the public phone number.'},'PUBLISH test')
assert updated['clinics'][0]['intake_reviewed_on']=='2026-09-01'
assert display_intake_status(updated['clinics'][0],now.date())=='needs_review'
print('PASS: actual manual phone correction preserves old intake freshness')
assert not usable_page('<html><div id="root"></div><noscript>You need to enable JavaScript to run this app.</noscript></html>')
assert not usable_page('<html><p>You need to enable JavaScript to run this app.</p></html>')
assert usable_page('<p>Take just a moment to read this. Our clinic is accepting new patients for ongoing family practice.</p>')
assert usable_page('<p>Not accepting new patients.</p>')
secondary=copy.deepcopy(c);secondary['intake_verification']['tier']='third_party';secondary['intake_verification']['reviewed_on']='2020-01-01'
assert display_intake_status(secondary,now.date())=='needs_review'
assert display_expiry(secondary,now.date()) is None
secondary['intake_verification']['reviewed_on']='2026-11-01'
assert display_intake_status(secondary,now.date())=='reported'
assert display_expiry(secondary,now.date())=='2026-12-17'
assert display_intake_status(secondary,dt.date(2026,12,17))=='needs_review'
print('PASS: JavaScript-only shells rejected, brief/prose clinic pages preserved, stale secondary evidence expires in Python')
