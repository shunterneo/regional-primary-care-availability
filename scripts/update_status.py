#!/usr/bin/env python3
"""Reviewed update with fail-closed evidence requirements. Public clinic info only."""
from __future__ import annotations
import argparse,datetime,json
from common import ROOT, STATUSES, is_url, ongoing_eligible
from evidence_policy import host
from auto_evidence import explicit_longitudinal, decisive_statement
p=argparse.ArgumentParser(description='Update reviewed public primary-care intake details.')
p.add_argument('--id',required=True)
p.add_argument('--status',required=True,choices=[s for s in STATUSES if s!='needs_review'])
p.add_argument('--source',required=True)
p.add_argument('--detail',required=True)
p.add_argument('--reviewer-note',required=True)
p.add_argument('--evidence-quote',default='',help='Exact clinic-published statement for accepting')
p.add_argument('--verification-scope',default='unverified',choices=['location','named_clinician','program','unverified'])
a=p.parse_args()
if not is_url(a.source):p.error('Source must be HTTPS')
if len(a.detail.strip())<12 or len(a.reviewer_note.strip())<16:p.error('Provide meaningful intake detail and an audit note')
path=ROOT/'data'/'clinics.json';db=json.loads(path.read_text()); matches=[c for c in db['clinics'] if c['id']==a.id]
if len(matches)!=1:p.error('Expected exactly one existing clinic ID')
c=matches[0]
if not ongoing_eligible(c) and a.status not in ('unknown','reported'):
    p.error('Walk-in-only or unverified care model cannot be an ongoing-care opening or closure')
if a.status=='accepting':
    if a.verification_scope not in ('location','named_clinician'):
        p.error('Green requires explicit site-specific or named-physician scope')
    if not host(a.source) or host(a.source)!=host(c.get('clinic_url')):
        p.error("Green requires an original clinic-owned webpage, not a secondary directory or unrelated domain")
    candidate=decisive_statement(a.evidence_quote)
    if candidate is None or candidate.get('status')!='accepting':
        p.error('The exact first-party statement must clearly say the clinic is ACCEPTING; no ambiguity or negative wording')
    if not explicit_longitudinal(a.evidence_quote):
        p.error('Green requires a verbatim clinic notice that explicitly specifies ongoing family doctor or NP care')
    if len(a.evidence_quote.strip())<24:
        p.error('Verbatim public clinic notice too short')
old=c['status'];date=datetime.date.today().isoformat()
c.update(status=a.status,evidence_url=a.source,intake_detail=a.detail.strip(),last_reviewed=date,intake_reviewed_on=date,review_basis=a.reviewer_note.strip())
c['intake_verification']={
    'tier':'clinic_first_party' if a.status=='accepting' else 'unverified',
    'scope':a.verification_scope if a.status=='accepting' else 'unverified',
    'reviewed_on':date if a.status=='accepting' else None,
    'source_url':a.source,
    'method':'reviewer_verified_public_source' if a.status=='accepting' else 'manual_review',
    'finding':a.evidence_quote.strip() if a.status=='accepting' else a.detail.strip(),
    'telephone_confirmed':False,'enrolment_guaranteed':False,
}
db['data_as_of']=date
path.write_text(json.dumps(db,indent=2,ensure_ascii=False)+'\n')
log=ROOT/'data'/'review_history.json';history=json.loads(log.read_text());history.append({
    'date':date,'clinic_id':c['id'],'clinic_name':c['name'],'old_status':old,'new_status':a.status,
    'source':a.source,'type':'manual_review_with_evidence_gate','reviewer_note':a.reviewer_note.strip(),
    'evidence_quote':a.evidence_quote.strip()[:500]})
log.write_text(json.dumps(history,indent=2,ensure_ascii=False)+'\n')
print(f'Reviewed intake status {c["id"]}: {old} -> {a.status}')
