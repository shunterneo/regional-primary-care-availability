#!/usr/bin/env python3
import sys,collections,datetime
from common import load_data, STATUSES,CITY_COORDS,km,is_url
D=load_data(); xs=D['clinics']; assert len(xs)>0
errors=[];ids=set();names=set();center=D['center']
for r in xs:
    id=r.get('id')
    if not id or id in ids:errors.append(f'duplicate/missing id {id}')
    ids.add(id)
    name=r.get('name','').strip(); key=(r['community'].lower(),name.lower(),r['address'].lower())
    if key in names:errors.append(f'duplicate listing {name}')
    names.add(key)
    if r['status'] not in STATUSES or r['status']=='needs_review':errors.append(f'bad stored status {id}')
    if r.get('operating_status','active') not in ('active','closed','archived','registry_listed'):errors.append(f'bad operating status {id}')
    if r['community'] not in CITY_COORDS:errors.append(f'unknown city coordinates {id}')
    else:
        dist=km(center['latitude'],center['longitude'],*CITY_COORDS[r['community']])
        if dist>75.01: errors.append(f'community outside boundary {id} ({dist:.1f} km)')
    if 'latitude' in r or 'longitude' in r:
        try:
            d=km(center['latitude'],center['longitude'],float(r['latitude']),float(r['longitude']))
            if d>center['radius_km']+.01:errors.append(f'clinic coordinate outside 75 km circle {id}: {d:.1f} km')
        except (KeyError,ValueError,TypeError):errors.append(f'invalid verified clinic coords for {id}')
    for fld in ('evidence_url','clinic_url'):
        if r.get(fld) and not is_url(r[fld]):errors.append(f'non-https URL in {id} ({fld})')
    if len(name)<3:errors.append(f'blank clinic name {id}')
    try:datetime.date.fromisoformat(r['last_reviewed'])
    except Exception: errors.append(f'bad last reviewed {id}')
print(f'Validation: {len(xs)} clinics, {len(set(r["community"] for r in xs))} communities, {len(errors)} errors')
for x in errors:print('ERROR:',x)
if errors:sys.exit(1)
