#!/usr/bin/env python3
"""Offline profile integration; synthetic writes occur only in temporary copies."""
import copy, datetime as dt, json, math, os, pathlib, shutil, subprocess, sys, tempfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import official_registry as registry
from profile_integrity import candidate_hash, coordinate_distance, same_office, PROFILE_VERSION
D=json.loads((ROOT/'data/clinics.json').read_text());center=D['center'];day=dt.date.today().isoformat();yesterday=(dt.date.today()-dt.timedelta(days=1)).isoformat()
f={'attributes':{'OGF_ID':987654321,'ENGLISH_NAME':'Synthetic Family Health Team','SERVICE_TYPE':'Family Health Team','ADDRESS_LINE_1':'100 Example Street','COMMUNITY':'Tillsonburg'},'geometry':{'x':-80.71,'y':42.86}}
row=next(iter(registry.collect([f],center).values()))
approval={'schema_version':PROFILE_VERSION,'candidate_hash':candidate_hash(row),'reviewed_on':day,'source_url':'https://example.test/office','reviewer_note':'Synthetic independently verified office and care model.','office_verified':True,'duplicates_reviewed':True,'care_model':'ongoing','care_model_finding':'Official office page describes ongoing family medicine care.'}
assert registry.valid_approval(approval,candidate_hash(row),day)
# An entire observation chain must be valid, not just its final timestamp.
invalid_chains=[['2000-01-01',day],['invalid'],None,[day,day],[day,yesterday],[(dt.date.today()+dt.timedelta(days=1)).isoformat()],[]]
for days in invalid_chains:
 for version in (PROFILE_VERSION,None,True):
  st={'seen':{row['id']:{'schema_version':version,'hash':candidate_hash(row),'days':days}},'publication_approvals':{row['id']:approval}}
  assert registry.process([f],copy.deepcopy(D),[],st,{},day)==[]
  assert st['seen'][row['id']]['days']==[day]
# Retain original precision at the 75-km boundary: rounding this point goes outside.
fedge=copy.deepcopy(f);fedge['geometry']={'x':-80.69032806090324,'y':43.53959285673019}
edge=next(iter(registry.collect([fedge],center).values()))
assert edge['latitude']==fedge['geometry']['y'] and edge['longitude']==fedge['geometry']['x']
coordinate_distance(center,edge['latitude'],edge['longitude'],registry.ROOT_URL)

for invalid in (True,False,None,{}, {**approval,'care_model_finding':''},{**approval,'schema_version':True},{**approval,'source_url':12},{**approval,'schema_version':0},{**approval,'office_verified':False},{**approval,'duplicates_reviewed':False},{**approval,'reviewed_on':(dt.date.today()+dt.timedelta(days=1)).isoformat()},{**approval,'reviewed_on':'2000-01-01'}):
 assert not registry.valid_approval(invalid,candidate_hash(row),day)
for field in ('name','address','community','clinic_type'):
 changed={**row,field:row[field]+' changed'}
 assert not registry.valid_approval(approval,candidate_hash(changed),day)
for lat,lon in ((float('nan'),-80.7),(42.86,float('inf')),(91,-80.7),(42.86,181),(True,-80.7),(44,-80.7)):
 try:coordinate_distance(center,lat,lon,'https://example.test/coords')
 except ValueError:pass
 else:raise AssertionError((lat,lon))
for source in ('',None,'http://example.test','https:///','https://user:password@example.test/','https://localhost/','https://127.0.0.1/','https://10.0.0.1/','https://[::1]/'):
 try:coordinate_distance(center,42.86,-80.7,source)
 except ValueError:pass
 else:raise AssertionError(source)
assert coordinate_distance(center,center['latitude'],center['longitude'],'https://example.test/coords')==0
# Exact distance gate does not add a hidden buffer.
from common import km
edge={'latitude':center['latitude'],'longitude':center['longitude'],'radius_km':km(center['latitude'],center['longitude'],43,-80.7)}
coordinate_distance(edge,43,-80.7,'https://example.test/coords')
try:coordinate_distance({**edge,'radius_km':edge['radius_km']-0.000001},43,-80.7,'https://example.test/coords')
except ValueError:pass
else:raise AssertionError('radius buffer')
assert same_office(row,{**row,'address':'100 Example St.'})
assert not same_office(row,{**row,'address':'200 Example Street'})
assert not same_office(row,{**row,'address':'100 Example Street Suite 2'})
assert not same_office({**row,'address':'100 Example Street Suite 1'},{**row,'address':'100 Example Street Suite 2'})
assert not same_office(row,{**row,'name':'Different Practice'})
assert registry.existing_clinic(row,[{**row,'id':'other'}])
assert not registry.existing_clinic(row,[{**row,'id':'other','address':'200 Example Street'}])
# No approval, legacy boolean, changed address, or same-day replay can publish.
for auth in (None,True,approval):
 db=copy.deepcopy(D);st={'seen':{},'publication_approvals':{row['id']:auth}};hist=[]
 assert registry.process([f],db,hist,st,{},day)==[]
 assert registry.process([f],db,hist,st,{},day)==[]
db=copy.deepcopy(D);st={'seen':{},'publication_approvals':{row['id']:approval}};hist=[]
assert registry.process([f],db,hist,st,{},yesterday)==[]
assert registry.process([f],db,hist,st,{},day)==[row['name']]
new=db['clinics'][-1];assert new['status']=='unknown' and new['coordinate_source'] and new['profile_approval']==approval
changed=copy.deepcopy(f);changed['attributes']['ADDRESS_LINE_1']='200 Changed Street';db2=copy.deepcopy(D)
assert registry.process([changed],db2,[],st,{},day)==[]
assert registry.process([changed],db2,[],st,{},(dt.date.today()+dt.timedelta(days=1)).isoformat())==[]

def command(folder,*args,success=True):
 result=subprocess.run([sys.executable,*args],cwd=folder,text=True,capture_output=True)
 assert (result.returncode==0)==success,(args,result.stdout,result.stderr)
 return result
with tempfile.TemporaryDirectory() as temp:
 target=pathlib.Path(temp)/'repo';shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('.git','__pycache__'))
 (target/'data/clinics.json').write_text(json.dumps(db))
 command(target,'scripts/validate.py');command(target,'tests/inventory_integrity_test.py')
 # Manual addition uses public-coordinate provenance and unknown intake.
 command(target,'scripts/add_clinic.py','--name','Synthetic Manual Clinic','--community','Tillsonburg','--address','101 Example Street','--clinic-type','MD','--intake-detail','No intake evidence verified','--source','https://example.test/office','--coordinate-source','https://example.test/coords','--reviewer-note','Synthetic independently verified public office','--care-model','unverified','--latitude','42.86','--longitude','-80.71')
 command(target,'scripts/validate.py');command(target,'tests/inventory_integrity_test.py')
 before_manual=(target/'data/clinics.json').read_bytes()
 all_before={x:(target/'data'/x).read_bytes() for x in ('clinics.json','review_history.json','extra_communities.json')}
 for status in ('accepting','reported','limited','waitlist','not_accepting'):
  command(target,'scripts/add_clinic.py','--name','Invalid status synthetic','--community','Tillsonburg','--address','999 Example Street','--clinic-type','MD','--intake-detail','Our family practice is accepting new patients.','--source','https://example.test/office','--coordinate-source','https://example.test/coords','--reviewer-note','Synthetic reviewed public office','--care-model','ongoing','--latitude','42.86','--longitude','-80.71','--status',status,success=False)
  assert all((target/'data'/x).read_bytes()==v for x,v in all_before.items())

 for badlat in ('nan','inf','91'):
  command(target,'scripts/add_clinic.py','--name','Invalid synthetic','--community','Tillsonburg','--address','999 Example Street','--clinic-type','MD','--intake-detail','Unknown intake','--source','https://example.test/office','--coordinate-source','https://example.test/coords','--reviewer-note','Synthetic invalid-coordinate attempt','--care-model','unverified','--latitude',badlat,'--longitude','-80.71',success=False)
  assert (target/'data/clinics.json').read_bytes()==before_manual
 records=json.loads((target/'data/clinics.json').read_text());manual=records['clinics'][-1]
 assert manual['care_model']=='unverified' and manual['status']=='unknown' and manual['coordinate_source']=='https://example.test/coords'
 for bad in (float('nan'),float('inf'),91):
  modified=copy.deepcopy(records);modified['clinics'][-1]['latitude']=bad
  (target/'data/clinics.json').write_text(json.dumps(modified));command(target,'scripts/validate.py',success=False)
 # Registry fetch failures persist health only and do not rewrite facts/history.
 (target/'data/clinics.json').write_text(json.dumps(records));statefile=target/'data/official_registry_state.json'
 initial={'seen':{'retained':{'row':{}}},'last_summary':{'published_registry_leads':0},'last_success':'2026-01-01'};statefile.write_text(json.dumps(initial))
 paths={'DB':target/'data/clinics.json','HISTORY':target/'data/review_history.json','FILE':statefile,'EXTRA':target/'data/extra_communities.json'}
 before={k:p.read_bytes() for k,p in paths.items() if k!='FILE'}
 with patch.multiple(registry,**paths),patch.object(registry,'fetch',side_effect=ValueError('synthetic unavailable')):
  registry.run()
 state=json.loads(statefile.read_text());assert state['last_error']=='synthetic unavailable' and state['consecutive_failures']==1 and state['seen']==initial['seen'] and state['last_success']==initial['last_success']
 assert all(p.read_bytes()==before[k] for k,p in paths.items() if k!='FILE')
 # HTTP 200 with malformed feature arrays must persist degradation, not crash or partially publish.
 for malformed in ([None],[f,None],[{'attributes':None,'geometry':{}}],[{'attributes':{},'geometry':{'x':float('nan'),'y':42.8}}]):
  class Response:
   content=b'{}'
   def raise_for_status(self):pass
   def json(self):return {'features':malformed}
  old_seen=json.loads(statefile.read_text())['seen']
  with patch.multiple(registry,**paths),patch.object(registry.requests,'get',return_value=Response()):assert registry.run()==0
  failed=json.loads(statefile.read_text());assert failed['last_error'] and failed['seen']==old_seen
  assert all(p.read_bytes()==before[k] for k,p in paths.items() if k!='FILE')
 with patch.multiple(registry,**paths),patch.object(registry,'fetch',return_value=[f]):registry.run()
 state=json.loads(statefile.read_text());assert state['last_error'] is None and state['consecutive_failures']==0 and state['last_success']!=initial['last_success']
print('PASS: version-bound approvals, office identity, finite/radius/provenance gates, generated/manual full integrity and persisted registry health; original data untouched')
