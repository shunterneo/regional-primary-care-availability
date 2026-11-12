#!/usr/bin/env python3
"""Deterministic integrity audit of ALL published public clinic records.
This is NOT telephone verification and DOES NOT assert live availability.
Run on every build; share full file for transparent quality follow-up.
"""
from __future__ import annotations
import csv, datetime as dt, json, re
from collections import Counter
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
from common import ROOT, load_data, CARE_MODELS
from evidence_policy import host, qualified_public_intake, display_intake_status

CIVIC=re.compile(r'\b\d{1,6}\b')
BAD_ADDRESS=re.compile(r'\b(address requires confirmation|tbd|not confirmed|unknown location)\b',re.I)

def review(c,day):
    issues=[]
    evidence=c.get('evidence_url','');website=c.get('clinic_url','')
    v=c.get('intake_verification') or {}
    tier=v.get('tier','unverified')
    if not CIVIC.search(c.get('address','')) or BAD_ADDRESS.search(c.get('address','')):
        issues.append('Unverified or incomplete street address')
    if not website or not website.startswith('https://'):
        issues.append('Missing/invalid clinic website link')
    if evidence and not evidence.startswith('https://'):
        issues.append('Invalid evidence URL')
    if tier in ('clinic_first_party','program_general'):
        if not evidence or not website or host(evidence)!=host(website):
            issues.append('CRITICAL: Claimed clinic/program source belongs to different organization')
        if v.get('source_url')!=evidence:
            issues.append('CRITICAL: Verification source URL does not match displayed evidence link')
    elif evidence and host(evidence)!=host(website):
        issues.append('Evidence source is another organization; label as referral/directory, not clinic intake')
    if c['status']=='accepting' and not qualified_public_intake(c,day):
        issues.append('CRITICAL: accepting lacks eligible current clinic-specific evidence')
    if c.get('care_model') not in CARE_MODELS:
        issues.append('CRITICAL: clinic care model missing/invalid')
    if c.get('operating_status') in ('closed','archived'):
        issues.append('Archived practice: exclude from active referral list')
    if not c.get('phone'):
        issues.append('No office telephone number in current record')
    if not c.get('clinic_address_verified'):
        issues.append('Street office location lacks prior source-verification flag')
    if tier in ('third_party','program_general','authoritative_secondary'):
        issues.append('Intake requires clinic-specific reconfirmation')
    if tier in ('unverified','conflicting_or_unconfirmed'):
        issues.append('No conclusive current intake evidence')
    return {
      'clinic_id':c['id'],'community':c['community'],'clinic':c['name'],'address':c['address'],
      'care_model':c.get('care_model','unverified'),'stored_intake':c['status'],
      'display_intake':display_intake_status(c,day),
      'evidence_tier':tier, 'source':evidence or website,'clinic_url':website,
      'source_checked':v.get('reviewed_on') or 'Not individually reviewed',
      'telephone_verified':'No','address_prior_source_supported':'Yes' if c.get('clinic_address_verified') else 'No',
      'issues':issues,
    }

def create_report(day=None):
    day=day or dt.datetime.now(ZoneInfo('America/Toronto')).date()
    d=load_data();records=[review(c,day) for c in d['clinics']]
    flagged=sum(bool(r['issues']) for r in records)
    critical=[r for r in records if any(z.startswith('CRITICAL:') for z in r['issues'])]
    summary={
      'audit_generated_on':day.isoformat(), 'audit_type':'structural/data-source integrity; not provider telephone verification',
      'records_examined':len(records),'records_with_review_flags':flagged,
      'critical_failures':len(critical),
      'display_status_counts':dict(Counter(r['display_intake'] for r in records)),
      'first_party_evidence_records':sum(r['evidence_tier']=='clinic_first_party' for r in records),
      'address_prior_source_supported_flags':sum(r['address_prior_source_supported']=='Yes' for r in records),
      'all_clinics_telephone_verified':False,
      'uncertain_records_are_not_live_openings':True,
    }
    return summary,records

def write_files():
    summary,records=create_report()
    folder=ROOT/'site'/'documents';folder.mkdir(parents=True,exist_ok=True)
    p=folder/'quality-audit.csv'
    columns=['clinic_id','community','clinic','address','care_model','stored_intake','display_intake','evidence_tier','source','clinic_url','source_checked','telephone_verified','address_prior_source_supported','review_flags']
    with p.open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
        for rec in records:
            writer.writerow({**{k:v for k,v in rec.items() if k in columns},'review_flags':' | '.join(rec['issues'])})
    (folder/'quality-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print('Audit:',summary)
    if summary['critical_failures']:
        raise ValueError('Critical source-integrity audit violations')
    return summary

if __name__=='__main__':write_files()
