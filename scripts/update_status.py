#!/usr/bin/env python3
"""Review-authorized intake update. The reviewed source must be explicit and current."""
import argparse,datetime,json
from common import ROOT,STATUSES,is_url,ongoing_eligible
p=argparse.ArgumentParser(description='Publish a reviewed intake change to the clinic source database.')
p.add_argument('--id',required=True,help='Clinic ID, e.g. c001')
p.add_argument('--status',required=True,choices=[s for s in STATUSES if s!='needs_review'])
p.add_argument('--source',required=True,help='Public HTTPS evidence URL checked by reviewer')
p.add_argument('--detail',required=True,help='Exact eligibility/intake notes, no client information')
p.add_argument('--reviewer-note',required=True,help='What was checked / why status can change')
a=p.parse_args()
if not is_url(a.source):p.error('--source must be HTTPS')
if len(a.detail.strip())<12:p.error('--detail requires meaningful explanation')
file=ROOT/'data'/'clinics.json';D=json.loads(file.read_text());matches=[x for x in D['clinics'] if x['id']==a.id]
if len(matches)!=1:p.error('Expected exactly one clinic for ID '+a.id)
r=matches[0]
if not ongoing_eligible(r) and a.status!='unknown':p.error('Cannot mark walk-in-only or unverified care model as accepting or closed to ongoing patient attachment')
before=r['status'];r['status']=a.status;r['evidence_url']=a.source;r['intake_detail']=a.detail.strip();r['last_reviewed']=datetime.date.today().isoformat();r['review_basis']=a.reviewer_note.strip()
D['data_as_of']=datetime.date.today().isoformat();file.write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n')
log=ROOT/'data'/'review_history.json';history=json.loads(log.read_text());history.append({'date':r['last_reviewed'],'clinic_id':a.id,'old_status':before,'new_status':a.status,'source':a.source,'reviewer_note':a.reviewer_note.strip()});log.write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n')
print(f'Updated {a.id} {before} -> {a.status}. Rebuild to regenerate website + Word + PDF.')
