"""Evidence-boundary regression for the three reviewed Brantford additions."""
import json,pathlib,sys
from datetime import date,timedelta
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evidence_policy import display_intake_status
rows=json.loads((ROOT/'data/clinics.json').read_text())['clinics']
by_id={r['id']:r for r in rows}
g,c,b=[by_id[k] for k in ('c211','c212','c213')]
for r in (g,c,b):
    assert r['care_model']=='both' and r['community']=='Brantford'
    assert 'latitude' not in r and 'longitude' not in r
    assert not r.get('auto_updates_enabled')
    assert not r.get('intake_verification',{}).get('telephone_confirmed')
    assert not r.get('intake_verification',{}).get('enrolment_guaranteed')
    assert len([x for x in rows if x.get('phone')==r['phone']])==1
review=date.fromisoformat(g['intake_verification']['reviewed_on'])
assert display_intake_status(g,review)=='not_accepting'
assert display_intake_status(g,review+timedelta(days=22))=='needs_review'
assert c['status']=='unknown' and b['status']=='unknown'
assert 'appointment' in c['intake_detail'].lower()
assert 'callback' in b['intake_detail'] and 'Unit C' in b['intake_detail'] and 'Unit 5' in b['intake_detail']
assert b['address']=='595 West Street' and b['address_conflict']
assert b['intake_verification']['tier']=='conflicting_or_unconfirmed'
print('PASS: reviewed Brantford additions preserve negative expiry, unknown intake, unit conflict, and approximate locations')
