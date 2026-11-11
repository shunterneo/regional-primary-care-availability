#!/usr/bin/env python3
"""Publish only two-day, first-party, unambiguous public clinic claims.

No AI or news output is used. No client data is consumed or published.
"""
from __future__ import annotations
import json, datetime as dt
from common import ROOT
from auto_evidence import first_party,confirmed,explicit_longitudinal

D=ROOT/'data'; DB=D/'clinics.json'; SRC=D/'source_state.json'; HISTORY=D/'review_history.json'

def apply(database, source_state, history, day):
    changes=[]; refreshes=0
    owners={}
    for c in database['clinics']:
        owners.setdefault(c.get('evidence_url',''),[]).append(c['id'])
    for c in database['clinics']:
        if c.get('operating_status') in ('closed','archived') or c.get('auto_updates_enabled') is False:continue
        url=c.get('evidence_url','')
        rec=source_state.get('sources',{}).get(url,{})
        o=rec.get('auto_observation') or {}
        if not rec.get('official_first_party') or rec.get('last_error'):continue
        if not first_party(c,url,owners.get(url,[])):continue
        if not confirmed(o,day):continue
        decision=o.get('status')
        if decision not in ('accepting','not_accepting','closed'):continue
        # Walk-in registration is NEVER proof of attachment to a family doctor/NP.
        # Combined providers need the first-party *statement itself* to specify ongoing care.
        if decision!='closed':
            if c.get('care_model') not in ('ongoing','both'):continue
            if c.get('care_model')=='both' and not explicit_longitudinal(o.get('quote','')):continue
        prior=c.get('status','unknown')
        if decision=='closed':
            # A permanent practice closure archives its *office*, not merely intake.
            c['operating_status']='closed'
            c['archived_at']=day
            c['archived_reason']='Two daily checks of explicit permanent-closure notice on clinic-specific official webpage.'
            c['status']='unknown'
            c['last_reviewed']=day
            action='permanently closed'
        elif prior != decision:
            c['status']=decision
            c['last_reviewed']=day
            c['intake_detail']=('Official clinic page explicitly states: '+o['quote'])[:400]
            c['review_basis']='Automatic: stable unambiguous first-party statement checked on separate days; subject to clinic confirmation.'
            action=decision
        else:
            # Reconfirmation is meaningful but does not need a new history entry.
            try: age=(dt.date.fromisoformat(day)-dt.date.fromisoformat(c['last_reviewed'])).days
            except (ValueError,KeyError):age=999
            if age>=7:
                c['last_reviewed']=day
                c['review_basis']='Automatic weekly recheck of same first-party intake claim.'
                refreshes+=1
            continue
        history.append({'date':day,'clinic_id':c['id'],'clinic_name':c['name'],
            'old_status':prior,'new_status':action,'type':'automated_official_confirmation',
            'source':url,'evidence':o.get('quote','')[:320],
            'days_confirmed':o['days'][-2:],
            'reviewer_note':'Two separate-day checks of clinic-specific first-party statement; no AI/third-party evidence.'})
        changes.append({'id':c['id'],'name':c['name'],'action':action})
    if changes or refreshes:database['data_as_of']=day
    return changes,refreshes

def run():
    database=json.loads(DB.read_text());state=json.loads(SRC.read_text());history=json.loads(HISTORY.read_text())
    today=dt.date.today().isoformat()
    changes,refreshes=apply(database,state,history,today)
    if changes or refreshes:
        DB.write_text(json.dumps(database,indent=2,ensure_ascii=False)+'\n')
        HISTORY.write_text(json.dumps(history,indent=2,ensure_ascii=False)+'\n')
    print('Auto-publication:',{'confirmed_changes':len(changes),'reconfirmed':refreshes,'items':changes})
    return 0
if __name__=='__main__':raise SystemExit(run())
