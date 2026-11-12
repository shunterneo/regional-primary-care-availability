#!/usr/bin/env python3
"""Apply one explicit, authenticated workflow-dispatch edit; never execute input text."""
import copy,datetime,json,os
from common import ROOT,STATUSES,CARE_MODELS,CITY_COORDS,is_url
from evidence_policy import host
from auto_evidence import decisive_statement,explicit_longitudinal
ALLOWED={'name','community','address','phone','providers','status','care_model','intake_detail','clinic_url','application_url'}
def apply_edit(db,proposal,confirmation,actor='maintainer'):
    if not isinstance(proposal,dict) or proposal.get('version')!=1:raise ValueError('Unsupported edit format')
    cid=proposal.get('clinic_id')
    if confirmation!=f'PUBLISH {cid}':raise ValueError('Type PUBLISH followed by the clinic ID to confirm')
    matches=[c for c in db['clinics'] if c['id']==cid]
    if len(matches)!=1:raise ValueError('Clinic not found')
    old=matches[0];changes=proposal.get('changes',{});base=proposal.get('base',{})
    if not isinstance(changes,dict) or not changes or not set(changes)<=ALLOWED:raise ValueError('Missing or unsupported fields')
    if proposal.get('base_reviewed')!=old.get('last_reviewed'):raise ValueError('Record changed since draft opened; reload and review again')
    for key,value in changes.items():
        if key not in base or base[key]!=old.get(key,''):raise ValueError('Stale original value: '+key)
        if not isinstance(value,str) or len(value)>2000:raise ValueError('Invalid field value: '+key)
    source=proposal.get('source_url','');note=proposal.get('review_note','')
    if not is_url(source) or len(note.strip())<16:raise ValueError('Provide an HTTPS evidence source and meaningful review note')
    new=copy.deepcopy(old);new.update(changes)
    if new['status'] not in STATUSES or new['status']=='needs_review':raise ValueError('Invalid intake status')
    if new['care_model'] not in CARE_MODELS or new['community'] not in CITY_COORDS:raise ValueError('Unsupported care model or community')
    if len(new['name'].strip())<3 or not new['address'].strip():raise ValueError('Name and address required')
    for key in ('clinic_url','application_url'):
        if new.get(key) and not is_url(new[key]):raise ValueError('Links must use HTTPS')
    today=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    address_changed=any(k in changes for k in ('address','community'))
    if address_changed:
        if proposal.get('address_confirmed') is not True:raise ValueError('Confirm the new office address against the cited source')
        for key in ('latitude','longitude','coordinate_source','coordinate_quality','coordinate_reviewed_on'):new.pop(key,None)
        new.update(clinic_address_verified=True,address_verification_source=source,address_verified_on=today,location_quality='Address reviewed by maintainer; map uses approximate community until coordinates checked')
    intake_changed=any(k in changes for k in ('status','care_model','intake_detail','clinic_url','name','providers'))
    if intake_changed:
        scope=proposal.get('verification_scope','unverified');quote=proposal.get('evidence_quote','').strip()
        if new['status']=='accepting':
            decision=decisive_statement(quote)
            if scope not in ('location','named_clinician') or host(source)!=host(new.get('clinic_url')) or not host(source):raise ValueError('Advertised applications need clinic-owned evidence for this site or clinician')
            if not decision or decision.get('status')!='accepting' or not explicit_longitudinal(quote):raise ValueError('Provide the clinic statement explicitly inviting ongoing family doctor/NP applications')
            if proposal.get('conflict_resolved') is not True and old.get('intake_conflict'):raise ValueError('Resolve the recorded intake conflict before advertising applications')
            new['intake_conflict']=False
        tier='clinic_first_party' if new['status']=='accepting' else 'unverified'
        new.update(evidence_url=source,intake_verification={'tier':tier,'scope':scope,'reviewed_on':today,'source_url':source,'method':'reviewer_verified_public_source','finding':quote or new['intake_detail'],'telephone_confirmed':False,'enrolment_guaranteed':False})
    if new['care_model'] in ('walk_in_only','unverified') and new['status']!='unknown':raise ValueError('Walk-in or unverified care cannot advertise ongoing attachment')
    new.update(last_reviewed=today,review_basis=note,auto_updates_enabled=False,last_manual_edit={'date':today,'actor':actor,'source_url':source,'fields':sorted(changes)})
    if new['status']=='accepting' and not new.get('clinic_address_verified'):raise ValueError('Verify the office address before advertising applications')
    out=copy.deepcopy(db);out['clinics']=[new if c['id']==cid else c for c in out['clinics']];out['data_as_of']=today
    event={'date':today,'clinic_id':cid,'clinic_name':new['name'],'old_status':old['status'],'new_status':new['status'],'type':'site_editor_approved','actor':actor,'source':source,'reviewer_note':note,'changes':{k:{'old':old.get(k,''),'new':v} for k,v in changes.items()}}
    return out,event
if __name__=='__main__':
    raw=os.environ.get('CLINIC_EDIT','')
    if len(raw)>24000:raise SystemExit('Edit payload too large')
    p=ROOT/'data/clinics.json';log=ROOT/'data/review_history.json'
    try:db,event=apply_edit(json.loads(p.read_text()),json.loads(raw),os.environ.get('EDIT_CONFIRMATION',''),os.environ.get('GITHUB_ACTOR','maintainer'))
    except (ValueError,KeyError,TypeError) as e:raise SystemExit(str(e))
    history=json.loads(log.read_text());history.append(event)
    p.write_text(json.dumps(db,indent=2,ensure_ascii=False)+'\n');log.write_text(json.dumps(history,indent=2,ensure_ascii=False)+'\n');print('Applied reviewed clinic edit:',event['clinic_id'])
