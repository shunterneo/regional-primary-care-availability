#!/usr/bin/env python3
"""Prepare one consolidated GitHub Issue about *new* pending review items.

The issue contains PUBLIC information only, with no patient/client addresses.
"""
from __future__ import annotations
import argparse,datetime,json,os,pathlib
from common import ROOT
DATA=ROOT/'data'; STATE=DATA/'notification_state.json';OUT=ROOT/'review-notice.md'
p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--mark-notified',action='store_true');a=p.parse_args()
s=json.loads(STATE.read_text());known=set(s['notified'])
q1=json.loads((DATA/'review_queue.json').read_text())['items']
q2=json.loads((DATA/'discovery_queue.json').read_text())['items']
q3=json.loads((DATA/'directory_queue.json').read_text())['items']
q4=json.loads((DATA/'registry_audit_queue.json').read_text())['items']
new=[x for x in q1+q2+q3+q4 if x.get('review_status')=='pending' and x['id'] not in known][:80]
if a.prepare:
    OUT.write_text('# Public primary-care research — review required\n\n'
      +f'Generated: {datetime.date.today().isoformat()}  |  New leads/change notices: {len(new)}\n\n'
      +'These items are **not confirmed intake openings or closures**. Check original clinic information and specific eligibility before publication. CPSO/CNO records are professional-registration sources, not accepting-patient lists.\n\n'
      +''.join(f"- `{i['id']}` — {i.get('title') or i.get('source_kind') or 'Source changed'} — {i.get('url') or i.get('news_link')}\n" for i in new[:80])
      +'\nDo not place patient identifiers or residential addresses in issue comments.\n',encoding='utf8')
    print('notice_count='+str(len(new)))
    print('new_ids='+','.join(i['id'] for i in new))
if a.mark_notified:
    s['notified']=sorted(known|{i['id'] for i in new})
    STATE.write_text(json.dumps(s,indent=2)+'\n')
    print(f'Marked {len(new)} new notices as reported')
