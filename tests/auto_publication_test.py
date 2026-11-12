#!/usr/bin/env python3
"""Offline evidence and lifecycle regression tests. No live websites or patients."""
import sys,copy,datetime as dt
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from auto_evidence import decisive_statement, observe, confirmed, first_party,explicit_longitudinal
from auto_publish import apply
from official_registry import collect,process

assert decisive_statement('We are now accepting new patients.')['status']=='accepting'
assert explicit_longitudinal('Our family practice is now accepting new patients')
assert not explicit_longitudinal('We are now accepting new patients')
assert not explicit_longitudinal('We accept walk-in patients for urgent family care appointments')
assert decisive_statement('We are no longer accepting new patients.')['status']=='not_accepting'
assert decisive_statement('We are not currently accepting new patients.')['status']=='not_accepting'
assert decisive_statement('Our clinic is permanently closed.')['status']=='closed'
assert decisive_statement('We are accepting new patients for selected doctors only.') is None
assert decisive_statement('We are accepting new patients. We are not accepting new patients.') is None
assert decisive_statement('New patient registration is available') is None
assert decisive_statement('Our clinic is temporarily closed.') is None
assert decisive_statement('The other clinic is accepting new patients.') is None
clinic={'id':'c900','name':'Example Clinic','community':'Tillsonburg','address':'1 Main St',
        'status':'unknown','clinic_url':'https://exampleclinic.ca/','evidence_url':'https://exampleclinic.ca/patients',
        'last_reviewed':'2026-11-09','care_model':'ongoing'}
assert first_party(clinic,clinic['evidence_url'],['c900'])
assert not first_party(clinic,clinic['evidence_url'],['c900','c901'])
assert not first_party(clinic,clinic['evidence_url'],['c900'],'https://another-site.ca')
assert not first_party({**clinic,'clinic_url':'https://211ontario.ca/'},clinic['evidence_url'],['c900'])
first=observe({},decisive_statement('Our family practice is now accepting new patients.'),'2026-11-10T13:00:00+00:00')
assert not confirmed(first,'2026-11-10')
second=observe(first,decisive_statement('Our family practice is now accepting new patients.'),'2026-11-11T13:00:00+00:00')
assert confirmed(second,'2026-11-11')
assert not confirmed(second,'2026-11-15')
assert not confirmed(observe(second,decisive_statement('We are not accepting new patients.'),'2026-11-12T13:00:00+00:00'),'2026-11-12')
source={'sources':{clinic['evidence_url']:{'official_first_party':True,'auto_observation':second,'last_error':None}}}
record={'clinics':[copy.deepcopy(clinic)],'data_as_of':'2026-11-09'}
history=[]
changes,_=apply(record,source,history,'2026-11-11')
assert len(changes)==1 and record['clinics'][0]['status']=='accepting' and record['clinics'][0]['intake_verification']['tier']=='clinic_first_party' and history[-1]['type']=='automated_official_confirmation'
assert not apply(record,source,history,'2026-11-11')[0]
assert len(history)==1
# Combined walk-in/ongoing provider cannot be auto-advertised on an ambiguous generic intake claim.
combo={**clinic,'care_model':'both','id':'c901'}
combo_observation={**second,'quote':'We are now accepting new patients.'}
combo_source={'sources':{clinic['evidence_url']:{'official_first_party':True,'auto_observation':combo_observation,'last_error':None}}}
combo_record={'clinics':[copy.deepcopy(combo)],'data_as_of':'2026-11-09'}
assert not apply(combo_record,combo_source,[],'2026-11-11')[0]
combo_source['sources'][clinic['evidence_url']]['auto_observation']={**second,'quote':'Our family practice is now accepting new patients'}
assert apply(combo_record,combo_source,[],'2026-11-11')[0]
walk={**clinic,'care_model':'walk_in_only','id':'c902'}
assert not apply({'clinics':[walk],'data_as_of':'2026-11-09'},combo_source,[],'2026-11-11')[0]
source['sources'][clinic['evidence_url']]['last_error']='site unavailable'
assert not apply(record,source,history,'2026-11-11')[0]
source['sources'][clinic['evidence_url']]['last_error']=None
close=observe({},decisive_statement('Our clinic is permanently closed.'),'2026-11-10T13:00:00+00:00')
close=observe(close,decisive_statement('Our clinic is permanently closed.'),'2026-11-11T13:00:00+00:00')
source['sources'][clinic['evidence_url']]['auto_observation']=close
changes,_=apply(record,source,history,'2026-11-11')
assert len(changes)==1 and record['clinics'][0]['operating_status']=='closed'
assert record['clinics'][0]['status']=='unknown' and not apply(record,source,history,'2026-11-11')[0]

center={'latitude':42.8654,'longitude':-80.7228,'radius_km':75}
fixture={'attributes':{'OGF_ID':123,'ENGLISH_NAME':'An Example Nurse Practitioner-Led Clinic',
    'SERVICE_TYPE':'Nurse Practitioner Led Clinic','ADDRESS_LINE_1':'100 Example Street',
    'COMMUNITY':'Tillsonburg'},'geometry':{'x':-80.71,'y':42.86}}
rows=collect([fixture],center)
assert len(rows)==1
assert not collect([{**fixture,'geometry':{'x':-79.0,'y':44.0}}],center)
register={'seen':{},'last_run':None}
base={'clinics':[], 'center':center, 'data_as_of':'2026-11-09'}
assert process([fixture],base,[],register,{},'2026-11-10')==[]
log=[];ex={}
added=process([fixture],base,log,register,ex,'2026-11-11')
assert len(added)==1 and base['clinics'][0]['status']=='unknown' and base['clinics'][0]['operating_status']=='registry_listed'
assert not process([fixture],base,log,register,ex,'2026-11-12')
assert len(log)==1
print('PASS: conservative official intake, two separate days, ambiguous/blocked pages, permanent closure archive, government-only unknown intake and no duplicates')
