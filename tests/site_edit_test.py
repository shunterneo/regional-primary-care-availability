"""Publishing guards: stale drafts, explicit consent, source validation and coordinate invalidation."""
import copy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from apply_site_edit import apply_edit
D=json.load(open(R/'data/clinics.json')); c=next(x for x in D['clinics'] if x['id']=='c001')
p={'version':1,'clinic_id':c['id'],'base_reviewed':c['last_reviewed'],'base':{'phone':c['phone']},'changes':{'phone':'519-555-0100'},'source_url':c['evidence_url'],'review_note':'Fixture review of a public office phone correction.'}
new,event=apply_edit(D,p,'PUBLISH c001','fixture');assert next(x for x in new['clinics'] if x['id']=='c001')['phone']=='519-555-0100';assert c['phone']!='519-555-0100';assert event['changes']['phone']['old']==c['phone']
def rejects(x,confirm='PUBLISH c001'):
 try:apply_edit(D,x,confirm)
 except ValueError:return
 raise AssertionError('Unsafe edit accepted')
rejects(p,'c001');q=copy.deepcopy(p);q['base']['phone']='stale';rejects(q)
q=copy.deepcopy(p);q['changes']['latitude']='0';rejects(q)
q=copy.deepcopy(p);q['source_url']='javascript:alert(1)';rejects(q)
q=copy.deepcopy(p);q['changes']={'address':'123 Test Street'};q['base']={'address':c['address']};rejects(q);q['address_confirmed']=True;out,_=apply_edit(D,q,'PUBLISH c001');changed=next(x for x in out['clinics'] if x['id']=='c001');assert 'latitude' not in changed and changed['address_verification_source']==q['source_url']
q=copy.deepcopy(p);q['changes']={'intake_detail':'Accepting all new patients'};q['base']={'intake_detail':c['intake_detail']};rejects(q) # cannot retain green on edited intake without source wording
print('PASS: explicit confirmation, stale values, field allowlist, HTTPS evidence, green evidence gate, and stale-pin removal')
