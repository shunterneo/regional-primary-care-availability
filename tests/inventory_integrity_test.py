#!/usr/bin/env python3
"""Validate live inventory rules without forbidding later sourced maintainer corrections."""
import sys,json,datetime as dt,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_inventory import create_report,review
from evidence_policy import qualified_public_intake
D=json.load(open(ROOT/'data/clinics.json'));C={c['id']:c for c in D['clinics']};T=dt.date.fromisoformat(D['data_as_of'])
summary,rows=create_report(T)
assert len(C)==len(D['clinics']) and len(C)>=96
assert summary['critical_failures']==0
for c in C.values():
 if c['status']=='accepting':
  # Evaluate on that intake review's actual date; builds may run after evidence expires.
  assert qualified_public_intake(c,dt.date.fromisoformat(c['intake_verification']['reviewed_on']))
  assert c['clinic_address_verified'] and not c.get('intake_conflict')
 if c.get('clinic_address_verified'):assert c.get('address_verification_source')
 if 'latitude'in c:assert 'longitude'in c and c.get('coordinate_source')
assert summary['display_status_counts'].get('accepting',0)==sum(qualified_public_intake(c,T) for c in C.values())
# Regression: unrelated first-party host is never silently treated as original evidence.
original=next(c for c in C.values() if (c.get('intake_verification')or{}).get('tier')=='clinic_first_party')
wrong=copy.deepcopy(original);wrong['evidence_url']='https://unrelated.example.org/notice'
assert any('CRITICAL' in s for s in review(wrong,T)['issues'])
print('PASS: live integrity, evidence gating, source attribution and coordinate provenance')
