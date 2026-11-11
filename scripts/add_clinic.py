#!/usr/bin/env python3
"""Add an independently VERIFIED public clinic; excludes residential/client addresses."""
from __future__ import annotations
import argparse,datetime,json,re
from common import ROOT,CITY_COORDS,km,is_url
p=argparse.ArgumentParser(description='Publish a manually verified public primary-care practice.')
for arg in ('name','community','address','clinic-type','intake-detail','source','reviewer-note'):
    p.add_argument('--'+arg,required=True)
p.add_argument('--status',choices=['accepting','reported','limited','waitlist','not_accepting','unknown'],default='unknown')
p.add_argument('--latitude',type=float,required=True,help='PUBLIC CLINIC location, not a patient address')
p.add_argument('--longitude',type=float,required=True,help='PUBLIC CLINIC location, not a patient address')
p.add_argument('--phone',default='');p.add_argument('--providers',default='');a=p.parse_args()
if not is_url(a.source):p.error('Source must be an HTTPS URL')
if not (40 < a.latitude < 46 and -84 < a.longitude < -78):p.error('Geographic coordinates appear to be outside Southwestern Ontario')
Dpath=ROOT/'data'/'clinics.json';D=json.loads(Dpath.read_text());center=D['center']
distance=km(center['latitude'],center['longitude'],a.latitude,a.longitude)
if distance>center['radius_km']:p.error(f'Clinic is {distance:.1f} km away, outside the 75 km circle')
if len(a.reviewer_note.strip())<15:p.error('Explain how clinic, coordinates, intake and eligibility were verified')
if len(a.address.strip())<6:p.error('Enter a real public clinic street address')
if a.status!='unknown' and len(a.intake_detail.strip())<15:p.error('Non-unknown status requires a specific intake evidence statement')
for c in D['clinics']:
    if c['name'].casefold()==a.name.casefold() and c['community'].casefold()==a.community.casefold():p.error('Potential duplicate clinic name/community; review existing record first')
extra=ROOT/'data'/'extra_communities.json';EX=json.loads(extra.read_text())
if a.community not in CITY_COORDS:EX[a.community]=[a.latitude,a.longitude];extra.write_text(json.dumps(EX,indent=2)+'\n')
ids=[int(c['id'][1:]) for c in D['clinics'] if re.fullmatch('c[0-9]+',c['id'])]
ident='c'+str(max(ids,default=0)+1).zfill(3);today=datetime.date.today().isoformat()
D['clinics'].append({'id':ident,'name':a.name,'community':a.community,'address':a.address,'clinic_type':a.clinic_type,'status':a.status,'intake_detail':a.intake_detail,'phone':a.phone,'providers':a.providers,'evidence_url':a.source,'clinic_url':a.source,'source_published':'','last_reviewed':today,'location_quality':'verified public clinic coordinate; user supplied','community_distance_km':round(distance,1),'latitude':a.latitude,'longitude':a.longitude,'notes':'','review_basis':a.reviewer_note})
D['data_as_of']=today;Dpath.write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n')
log=ROOT/'data'/'review_history.json';history=json.loads(log.read_text());history.append({'date':today,'clinic_id':ident,'old_status':'not listed','new_status':a.status,'source':a.source,'reviewer_note':a.reviewer_note});log.write_text(json.dumps(history,indent=2)+'\n')
print(f'Added {ident}, {a.name}, {distance:.1f} km from 96 Tillson Avenue; run validate.py and build.py')
