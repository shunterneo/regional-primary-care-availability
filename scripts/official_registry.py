#!/usr/bin/env python3
"""Collect Ontario Ministry of Health-listed program sites for independent review.

Government registry only confirms an official listing, NOT a live accepting roster
or operational status. Publication requires an independent office approval as well
as two daily observations; many program addresses are not primary-care clinics.
Data licensed under the Open Government Licence – Ontario.
"""
from __future__ import annotations
import datetime as dt, json, re, hashlib, requests
from common import ROOT, km

ROOT_URL='https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open09/MapServer/26'
QURL=ROOT_URL+'/query'
DATA=ROOT/'data';FILE=DATA/'official_registry_state.json';DB=DATA/'clinics.json';HISTORY=DATA/'review_history.json';EXTRA=DATA/'extra_communities.json'
CATEGORIES={
    'community health centre':'CHC','family health team':'FHT','family health team - contract':'FHT','nurse practitioner led clinic':'NP','nurse practitioner-led clinic':'NP',
}

def normalized(s):return re.sub(r'[^a-z0-9]','',str(s or '').lower())

def collect(features, center):
    """Pure strict validation, one official point record per ID."""
    rows={}
    for feature in features:
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
                   'latitude':round(lat,6),'longitude':round(lon,6),'distance':round(d,1),'registry_id':ogf}
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
    if result.get('error') or result.get('exceededTransferLimit'):raise ValueError('Registry error or incomplete response')
    if not isinstance(result.get('features'),list):raise ValueError('No registry features returned')
    return result['features']

def existing_clinic(row, clinics):
    n=normalized(row['name']);adr=normalized(row['address']);cm=normalized(row['community'])
    for c in clinics:
        if c['id']==row['id']:return True
        if normalized(c['community']) != cm:continue
        cn=normalized(c['name']);ca=normalized(c['address'])
        # Avoid adding the government program beside an already-listed same physical site.
        if cn and (n==cn or n in cn or cn in n):return True
        if ca and (adr==ca or (len(ca)>8 and (adr.startswith(ca) or ca.startswith(adr)))):return True
    return False

def process(features, db, history, state, extra, day):
    additions=[];discovered=collect(features,db['center'])
    seen=state.setdefault('seen',{})
    active={}
    for ident,row in discovered.items():
        fingerprint=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
        old=seen.get(ident,{})
        dates=old.get('days',[]) if old.get('hash')==fingerprint else []
        if dates:
            diff=(dt.date.fromisoformat(day)-dt.date.fromisoformat(dates[-1])).days
            if diff<0 or diff>5:dates=[]
        if day not in dates: dates.append(day)
        active[ident]={'hash':fingerprint,'days':dates[-3:],'row':row}
        # A government program may be an administrative, youth or diabetes office.
        # Repeated observations cannot establish that it offers ongoing primary care.
        # Retain every lead for review; only an independent office review may publish it.
        if not state.get('publication_approvals', {}).get(ident):continue
        if len(dates)<2 or existing_clinic(row,db['clinics']):continue
        c={'id':ident,'name':row['name'],'community':row['community'],'address':row['address'],
           'clinic_type':row['clinic_type'],'care_model':'ongoing','care_model_basis':'Ontario Ministry of Health primary-care program classification; walk-in services not determined.','care_model_source':ROOT_URL,'status':'unknown','operating_status':'registry_listed',
           'intake_detail':'Listed in Ontario Ministry of Health registry; current operation and new-patient intake require confirmation.',
           'phone':'','providers':'','evidence_url':ROOT_URL,'clinic_url':ROOT_URL,
           'source_published':'','last_reviewed':day,
           'location_quality':'Ontario government public registry coordinates (planning accuracy only)',
           'community_distance_km':row['distance'],'latitude':row['latitude'],'longitude':row['longitude'],
           'notes':'Government listing, not guaranteed current practice or accepting patients.',
           'review_basis':'Automatically imported from the Ontario MOH registry after two separate daily observations. Intake and current operation unconfirmed.',
           'auto_updates_enabled':False}
        db['clinics'].append(c)
        if row['community'] not in extra:extra[row['community']]=[row['latitude'],row['longitude']]
        history.append({'date':day,'clinic_id':ident,'clinic_name':row['name'],'old_status':'not listed',
                        'new_status':'registry listed (intake unknown)','type':'automated_government_registry_listing',
                        'source':ROOT_URL, 'reviewer_note':'Ontario Ministry of Health registry, seen on two different days; not proof of active intake.'})
        additions.append(row['name'])
    state['seen']=active
    state['last_run']=day
    state['last_summary']={'government_records_in_region':len(discovered),'published_registry_leads':len(additions)}
    if additions:db['data_as_of']=day
    return additions

def run():
    day=dt.date.today().isoformat()
    db=json.loads(DB.read_text());hist=json.loads(HISTORY.read_text());st=json.loads(FILE.read_text());extra=json.loads(EXTRA.read_text())
    try:features=fetch()
    except (requests.RequestException,ValueError) as err:
        print('Ontario registry unavailable; preserving all current entries:',str(err)[:140]);return 0
    additions=process(features,db,hist,st,extra,day)
    FILE.write_text(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
    if additions:
        DB.write_text(json.dumps(db,ensure_ascii=False,indent=2)+'\n')
        HISTORY.write_text(json.dumps(hist,ensure_ascii=False,indent=2)+'\n')
        EXTRA.write_text(json.dumps(extra,ensure_ascii=False,indent=2)+'\n')
    print('Ontario official registry:',st['last_summary']);return 0
if __name__=='__main__':raise SystemExit(run())
