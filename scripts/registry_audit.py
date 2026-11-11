#!/usr/bin/env python3
"""Weekly, human-verified CPSO/CNO register audit task.

Neither regulator has a confirmed, supported bulk API integrated into this project.
Do not scrape regulated registers or claim they indicate patient acceptance.
"""
from __future__ import annotations
import datetime as dt,json,hashlib
from common import ROOT
DATA=ROOT/'data'; STATE=DATA/'registry_audit_state.json';QUEUE=DATA/'registry_audit_queue.json'
REGIONS=[
    ('Oxford and nearby communities','Tillsonburg, Woodstock, Ingersoll, Norwich, Courtland, Otterville, Tavistock'),
    ('Elgin and Norfolk','St. Thomas, Aylmer, Straffordville, Delhi, Simcoe, Waterford, Port Burwell, Port Rowan'),
    ('London and Middlesex','London, Ilderton, Strathroy, Mount Brydges, Ailsa Craig'),
    ('Brant and Waterloo/Perth edge','Brantford, Paris, Burford, Cambridge, Ayr, Kitchener, Waterloo, Stratford, New Hamburg'),
]
URLS={
 'CPSO':'https://register.cpso.on.ca/Advanced-Search01/',
 'CNO':'https://registry.cno.org/',
}

def prepare(state,queue,day,force=False):
    date=dt.date.fromisoformat(day)
    # Generate one task a week, not a flood of alerts on every daily run.
    if date.weekday()!=0 and not force:return 0
    iso=date.isocalendar();week=f'{iso.year}-W{iso.week:02d}'
    if state.get('last_week')==week:return 0
    i=(iso.week-1)%len(REGIONS);region,locations=REGIONS[i]
    ident=hashlib.sha256(('cpso-cno-'+week).encode()).hexdigest()[:18]
    if ident not in {x['id'] for x in queue['items']}:
        queue['items'].append({'id':ident,'detected_at':day,'title':'Monthly-cycle registry cross-check — '+region,
          'url':URLS['CPSO'],'second_url':URLS['CNO'],'region':region,'locations':locations,
          'review_status':'pending','proposed_action':'Manually inspect public CPSO family-physician and CNO nurse-practitioner practice-location records; compare with active office list. Independently verify any unlisted address and whether ongoing primary care is offered.',
          'intake_status':'not provided by registries',
          'note':'Official registers do NOT verify patient acceptance. No automated scraping or registry data ingestion.'})
    state['last_week']=week;state['last_run']=day
    return 1

def run():
    day=dt.date.today().isoformat()
    state=json.loads(STATE.read_text());queue=json.loads(QUEUE.read_text());n=prepare(state,queue,day)
    STATE.write_text(json.dumps(state,indent=2)+'\n')
    QUEUE.write_text(json.dumps(queue,indent=2)+'\n')
    print('Professional register manual audit:',{'queued':n,'week':state.get('last_week')})

if __name__=='__main__':run()
