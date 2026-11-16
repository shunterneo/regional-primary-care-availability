#!/usr/bin/env python3
"""Collect Ontario Ministry of Health-listed program sites for independent review.

Government registry only confirms an official listing, NOT a live accepting roster
or operational status. Publication requires an independent office approval as well
as two daily observations; many program addresses are not primary-care clinics.
Data licensed under the Open Government Licence – Ontario.
"""
from __future__ import annotations
import datetime as dt, json, re, requests, math
from common import ROOT, km, is_url
from profile_integrity import PROFILE_VERSION, candidate_hash, same_office, public_https_url

ROOT_URL='https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open09/MapServer/26'
QURL=ROOT_URL+'/query'
DATA=ROOT/'data';FILE=DATA/'official_registry_state.json';DB=DATA/'clinics.json';HISTORY=DATA/'review_history.json';EXTRA=DATA/'extra_communities.json'
CATEGORIES={
    'community health centre':'CHC','family health team':'FHT','family health team - contract':'FHT','nurse practitioner led clinic':'NP','nurse practitioner-led clinic':'NP',
}

def normalized(s):return re.sub(r'[^a-z0-9]','',str(s or '').lower())

def validate_features(features):
    if not isinstance(features,list):raise ValueError('Registry features must be an array')
    for feature in features:
        if not isinstance(feature,dict) or not isinstance(feature.get('attributes'),dict) or not isinstance(feature.get('geometry'),dict):
            raise ValueError('Malformed registry feature/attributes/geometry')
        for field in ('x','y'):
            value=feature['geometry'].get(field)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError('Malformed registry coordinate')
    return features

def observation_days(old, fingerprint, day):
    """Reject the entire stale/malformed observation chain, never repair it into proof."""
    reset=[day]
    if not isinstance(old,dict) or old.get('hash')!=fingerprint or type(old.get('schema_version')) is not int or old['schema_version']!=PROFILE_VERSION:return reset
    days=old.get('days')
    if not isinstance(days,list) or not days or any(not isinstance(x,str) for x in days):return reset
    try:
        dates=[dt.date.fromisoformat(x) for x in days];today=dt.date.fromisoformat(day)
    except (TypeError,ValueError):return reset
    if any(x.isoformat()!=raw for x,raw in zip(dates,days)):return reset
    if dates!=sorted(set(dates)) or dates[-1]>today or (today-dates[0]).days>5:return reset
    if any(not 0<(b-a).days<=5 for a,b in zip(dates,dates[1:])):return reset
    return (days if day in days else days+[day])[-3:]

def collect(features, center):
    """Pure strict validation, one official point record per ID."""
    rows={}
    for feature in validate_features(features):
        a=feature.get('attributes') or {}; geom=feature.get('geometry') or {}
        typ=str(a.get('SERVICE_TYPE','')).strip().casefold()
        clinic_type=CATEGORIES.get(typ)
        if not clinic_type:continue
        name=str(a.get('ENGLISH_NAME') or '').strip()
        community=str(a.get('COMMUNITY') or '').strip().title()
        address=str(a.get('ADDRESS_LINE_1') or '').strip()
        ogf=str(a.get('OGF_ID') or '')
        try:lon=float(geom['x']);lat=float(geom['y'])
        except (ValueError,TypeError,KeyError):continue
        if not (len(name)>4 and len(community)>2 and len(address)>5 and ogf and -82<lon<-79 and 42<lat<44.5):continue
        d=km(center['latitude'],center['longitude'],lat,lon)
        if d>center['radius_km']:continue
        # A complete physical address must have a civic number.
        if not re.search(r'\b\d{1,6}\b',address):continue
        key='moh-'+normalized(ogf)
        if len(key)>60:continue
        rows[key]={'id':key,'name':name,'community':community,'address':address,'clinic_type':clinic_type,
                   'latitude':lat,'longitude':lon,'distance':round(d,1),'registry_id':ogf}
    return rows

def fetch():
    # Query geographic bounding box only; input is a PUBLIC REGION, no patient address.
    p={'where':'1=1','geometry':'-81.71,42.18,-79.73,43.55','geometryType':'esriGeometryEnvelope',
       'inSR':'4326','spatialRel':'esriSpatialRelIntersects','outFields':
       'OGF_ID,ENGLISH_NAME,SERVICE_TYPE,ADDRESS_LINE_1,COMMUNITY',
       'outSR':'4326','returnGeometry':'true','f':'json','resultRecordCount':2000}
    response=requests.get(QURL,params=p,headers={'User-Agent':'OntarioPrimaryCareRegistryMonitor/1.0 public sites only'},timeout=(8,35))
    response.raise_for_status()
    if len(response.content)>8_000_000:raise ValueError('Unexpected registry response size')
    result=response.json()
    if not isinstance(result,dict):raise ValueError('Malformed registry response object')
    if result.get('error') or result.get('exceededTransferLimit'):raise ValueError('Registry error or incomplete response')
    if not isinstance(result.get('features'),list) or not result['features']:raise ValueError('No registry features returned')
    return result['features']

def existing_clinic(row, clinics):
    # Name-only, same-building and address-prefix matches are ambiguous, not IDs.
    return any(c['id']==row['id'] or same_office(row,c) for c in clinics)

def valid_approval(approval, fingerprint, day):
    """Only explicit, recent review of this exact version may publish a profile.

    Required fields: schema_version, candidate_hash, reviewed_on, source_url,
    reviewer_note, office_verified=True, duplicates_reviewed=True, care_model.
    For ongoing/both, care_model_finding must quote/describe the reviewed care
    evidence at source_url. Approval expires after 30 days; changes require review.
    Legacy booleans are not approvals. No automatic migration or approval creation.
    """
    if not isinstance(approval,dict):return False
    if type(approval.get('schema_version')) is not int or approval['schema_version']!=PROFILE_VERSION or approval.get('candidate_hash')!=fingerprint:return False
    if approval.get('office_verified') is not True or approval.get('duplicates_reviewed') is not True:return False
    if approval.get('care_model') not in ('ongoing','both','unverified'):return False
    if approval['care_model']!='unverified' and (not isinstance(approval.get('care_model_finding'),str) or len(approval['care_model_finding'].strip())<15):return False
    if not public_https_url(approval.get('source_url')):return False
    if not isinstance(approval.get('reviewer_note'),str) or len(approval['reviewer_note'].strip())<15:return False
    try:age=(dt.date.fromisoformat(day)-dt.date.fromisoformat(approval['reviewed_on'])).days
    except (KeyError,ValueError,TypeError):return False
    return 0<=age<=30

def process(features, db, history, state, extra, day):
    additions=[];discovered=collect(features,db['center'])
    seen=state.get('seen') if isinstance(state.get('seen'),dict) else {}
    active={}
    for ident,row in discovered.items():
        fingerprint=candidate_hash(row)
        old=seen.get(ident,{})
        dates=observation_days(old,fingerprint,day)
        active[ident]={'schema_version':PROFILE_VERSION,'hash':fingerprint,'days':dates,'row':row}
        # A government program may be an administrative, youth or diabetes office.
        # Repeated observations cannot establish that it offers ongoing primary care.
        # Retain every lead for review; only an independent office review may publish it.
        approvals=state.get('publication_approvals')
        approval=approvals.get(ident) if isinstance(approvals,dict) else None
        if not valid_approval(approval,fingerprint,day):continue
        if len(dates)<2 or existing_clinic(row,db['clinics']):continue
        c={'id':ident,'name':row['name'],'community':row['community'],'address':row['address'],
           'clinic_type':row['clinic_type'],'care_model':approval['care_model'],'care_model_basis':approval.get('care_model_finding') or 'Care model remains unverified; no ongoing-care claim.','care_model_source':approval['source_url'],'status':'unknown','operating_status':'registry_listed',
           'intake_detail':'Listed in Ontario Ministry of Health registry; current operation and new-patient intake require confirmation.',
           'phone':'','providers':'','evidence_url':ROOT_URL,'clinic_url':ROOT_URL,
           'source_published':'','last_reviewed':day,
           'location_quality':'Ontario government public registry coordinates (planning accuracy only)',
           'coordinate_source':ROOT_URL,'coordinate_checked_on':day,'profile_schema_version':PROFILE_VERSION,
           'community_distance_km':row['distance'],'latitude':row['latitude'],'longitude':row['longitude'],
           'notes':'Government listing, not guaranteed current practice or accepting patients.',
           'review_basis':'Independently reviewed office profile; stable registry record on two separate days. '+approval['reviewer_note'],
           'profile_approval':dict(approval),
           'auto_updates_enabled':False}
        db['clinics'].append(c)
        if row['community'] not in extra:extra[row['community']]=[row['latitude'],row['longitude']]
        history.append({'date':day,'clinic_id':ident,'clinic_name':row['name'],'old_status':'not listed',
                        'new_status':'registry listed (intake unknown)','type':'automated_government_registry_listing',
                        'source':ROOT_URL, 'reviewer_note':approval['reviewer_note'], 'profile_approval':dict(approval)})
        additions.append(row['name'])
    state['seen']=active
    state['last_run']=day
    state['last_summary']={'government_records_in_region':len(discovered),'published_registry_leads':len(additions)}
    if additions:db['data_as_of']=day
    return additions

def run():
    day=dt.date.today().isoformat()
    db=json.loads(DB.read_text());hist=json.loads(HISTORY.read_text());st=json.loads(FILE.read_text());extra=json.loads(EXTRA.read_text())
    attempt=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    st['last_attempt']=attempt
    try:
        features=fetch()
        additions=process(features,db,hist,st,extra,day)
    except (requests.RequestException,ValueError) as err:
        st['last_error']=str(err)[:300]
        st['consecutive_failures']=st.get('consecutive_failures',0)+1
        FILE.write_text(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
        print('Ontario registry unavailable; preserving all current entries:',str(err)[:140]);return 0
    st.update(last_success=attempt,last_error=None,consecutive_failures=0)
    FILE.write_text(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
    if additions:
        DB.write_text(json.dumps(db,ensure_ascii=False,indent=2)+'\n')
        HISTORY.write_text(json.dumps(hist,ensure_ascii=False,indent=2)+'\n')
        EXTRA.write_text(json.dumps(extra,ensure_ascii=False,indent=2)+'\n')
    print('Ontario official registry:',st['last_summary']);return 0
if __name__=='__main__':raise SystemExit(run())
