#!/usr/bin/env python3
"""Regression tests: no unverified intake ever appears green, site, DOCX or PDF."""
import sys,copy,datetime as dt,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from evidence_policy import qualified_public_intake,display_intake_status
D=json.loads((ROOT/'data/clinics.json').read_text());T=dt.date(2026,11,11)
assert len(D['clinics'])>=96
B={c['id']:c for c in D['clinics']}
assert sum(display_intake_status(c,T)=='accepting' for c in B.values()) == sum(qualified_public_intake(c,T) for c in B.values() if c['status']=='accepting')
for cid in ['c008','c011','c012','c013','c033']:
    if B[cid]['status']=='accepting':
        assert qualified_public_intake(B[cid],T), f'Unsubstantiated promotion {cid}'
assert B['c009']['status']=='unknown' and B['c009']['care_model']=='unverified'
assert all(B[cid]['status']!='accepting' for cid in ('c004','c005') if B[cid].get('intake_conflict'))
for cid in ['c015','c023']:
    if B[cid]['status']=='accepting':
        assert qualified_public_intake(B[cid],T), f'General matching notice promoted without clinic-specific evidence: {cid}'
for c in B.values():
    if display_intake_status(c,T)=='accepting':
        assert qualified_public_intake(c,T)
        assert c['intake_verification']['telephone_confirmed'] is False
        assert c['intake_verification']['enrolment_guaranteed'] is False
valid=copy.deepcopy(B['c001'])
assert display_intake_status(valid,T)=='accepting'
for mutate in [
    {'intake_verification':{}},
    {'intake_verification':{**valid['intake_verification'],'tier':'third_party'}},
    {'intake_verification':{**valid['intake_verification'],'scope':'program'}},
    {'intake_verification':{**valid['intake_verification'],'reviewed_on':None}},
    {'clinic_url':'https://some-other-host.example/'}
]:
    trial={**valid,**mutate}; assert display_intake_status(trial,T)!='accepting',mutate
assert display_intake_status(valid,T+dt.timedelta(days=22))=='needs_review'
assert display_intake_status({**valid,'care_model':'walk_in_only'},T)!='accepting'
print(f"PASS: {len(B)} records; verified applications dynamically gated; conflicting, third-party, stale and walk-in-only evidence never green")
# The manual review path also prevents an incorrect green label from an apparent negative quote.
import subprocess
p=ROOT/'scripts/update_status.py'
def manual(quote,scope='location'):
    return subprocess.run([sys.executable,str(p),
        '--id','c001','--status','accepting','--source',B['c001']['evidence_url'],
        '--detail','Primary-care application forms are explicitly accepted by the clinic.',
        '--reviewer-note','Reviewed official public clinic intake source and date with supporting details.',
        '--verification-scope',scope,'--evidence-quote',quote],
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
assert manual('Our clinic is not accepting new family medicine patients.').returncode!=0
assert manual('We are now accepting walk-in patients.').returncode!=0
assert manual('Our family practice is now accepting new patients.',scope='program').returncode!=0
# A successful reviewed change is checked separately in the existing approval fixture.
