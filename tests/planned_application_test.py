"""Planned application pathways are visible but cannot claim current operation."""
import copy,datetime,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from evidence_policy import qualified_public_intake,display_intake_status
j=json.loads((ROOT/'data/clinics.json').read_text());c=next(c for c in j['clinics'] if c['id']=='c228')
assert c['operating_status']=='planned' and 'planned' in c['name']
assert c['status']=='waitlist' and c['auto_updates_enabled'] is False
assert c['application_url']=='https://form.jotform.com/262283813217254'
assert display_intake_status(c,datetime.date(2026,11,18))=='waitlist'
fake=copy.deepcopy(c);fake['status']='accepting';fake['intake_verification']['tier']='clinic_first_party'
assert not qualified_public_intake(fake,datetime.date(2026,11,18))
assert display_intake_status(fake,datetime.date(2026,11,18))!='accepting'
print('PASS: planned application visible, labelled and never green accepting')
