import csv,json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
src=pathlib.Path('/mnt/data/Primary_Care_75km_Audit_2026-11-11.csv')
with src.open(encoding='utf-8-sig',newline='') as fh: rows=list(csv.DictReader(fh))
clinics=[]
for r in rows:
    clinics.append({
      'id':r['id'],'name':r['name'],'community':r['city'],'address':r['address'],
      'clinic_type':r['type'],'status':r['acceptance'],'intake_detail':r['detail'],
      'phone':r['phone'],'providers':r['providers'],'evidence_url':r['evidence_url'],
      'clinic_url':r['clinic_source'],'source_published':r['source_date'],
      'last_reviewed':'2026-11-11','location_quality':'community-centre estimate',
      'community_distance_km':float(r['approx_distance_km']),
      'notes':r['notes'],
      'review_basis':'Imported from the 2026-11-11 research audit; not re-confirmed by this automated build.',
    })
(ROOT/'data'/'clinics.json').write_text(json.dumps({'schema_version':1,'center':{'name':'96 Tillson Avenue, Tillsonburg','latitude':42.8654,'longitude':-80.7228,'radius_km':75},'data_as_of':'2026-11-11','clinics':clinics},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'data'/'source_state.json').write_text(json.dumps({'version':1,'sources':{}},indent=2)+'\n')
(ROOT/'data'/'review_queue.json').write_text(json.dumps({'version':1,'items':[]},indent=2)+'\n')
print(f'Seeded {len(clinics)} records')
