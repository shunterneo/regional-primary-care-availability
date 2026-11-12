#!/usr/bin/env python3
"""Regression tests from documented cross-organization and source-integrity failures."""
import sys, json, datetime as dt, copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_inventory import create_report, review
from evidence_policy import qualified_public_intake
D=json.load(open(ROOT/'data/clinics.json')); C={c['id']:c for c in D['clinics']}
assert len(C)>=96
T=dt.date(2026,11,11)
summary,rows=create_report(T)
assert summary['records_examined']>=96 and summary['critical_failures']==0
assert summary['display_status_counts']['accepting']==sum(qualified_public_intake(c,T) for c in C.values() if c['status']=='accepting')
assert all(qualified_public_intake(c,T) for c in C.values() if c['status']=='accepting')
# The wrong link that a user found must fail build validation even for non-green program data.
wrong=copy.deepcopy(C['c013']);wrong['evidence_url']='https://www.ocnplc.ca/patient-information/new-patients/'
assert any('CRITICAL' in s for s in review(wrong,T)['issues'])
assert C['c013']['evidence_url'].startswith('https://thamesvalleyfht.ca/')
assert C['c015']['address']=='2958 Greenfield Road'
assert C['c040']['phone']=='519-659-6399'
assert C['c024']['phone']=='226-666-0345'
assert all(C[cid]['status']!='accepting' for cid in ('c004','c005') if C[cid].get('intake_conflict'))
assert C['c096']['clinic_address_verified'] and C['c096']['care_model']=='ongoing'
# A multi-tenant building is not itself proof of a named accepting family physician.
assert C['c009']['status']!='accepting'
# Oxford NPLC's regional intake does not guarantee immediate placement at unfinished permanent Tillsonburg site.
assert C['c011']['status']!='accepting' or qualified_public_intake(C['c011'],T)
# A physician in an office must have a real street address.
assert C['c028']['address'].startswith('1807 Wonderland Road North')
# Doctor-specific phone number, not unrelated partner's phone.
assert C['c036']['phone']=='226-289-7231'
# Own official source currently not readable; do not present as clinic-verified intake.
assert C['c033']['status']!='accepting' or qualified_public_intake(C['c033'],T)
# Clinic link must not be a secondary municipal article when a real clinic site is known.
assert C['c012']['clinic_url']=='https://oxfordiamedical.com/'
print('PASS: structural audit, dynamically gated applications, cross-org mislink blocked, and specific office corrections')
