"""Offline stage-complete health checks; no network, writes, or publication."""
import copy,datetime as dt,hashlib,json,pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import monitor_health as m
NOW=dt.datetime(2026,11,16,1,tzinfo=dt.timezone.utc)
STAMP=NOW.isoformat()
E='https://clinic.example/patients';D='https://discovery.example/news'

def fixture():
 return dict(db={'clinics':[{'evidence_url':E}]},source_state={'last_run':STAMP,'last_summary':{'urls':2,'success':2,'failed':0},'sources':{u:{'last_success':STAMP,'last_attempt':STAMP,'last_error':None} for u in (E,D)}},now=NOW,
 discovery_sources=[{'url':D}],directory_config=[{'id':'dir','name':'Directory','url':'https://directory.example/','mode':'page'}],
 directory_state={'last_run':'2026-11-15','last_summary':{'sources':1,'success':1,'failed':0},'sources':{'dir':{'last_attempt':'2026-11-15','last_success':'2026-11-15','last_error':None,'entries':{'page':{}},'entry_count':1,'source_signature':hashlib.sha256(json.dumps({'url':'https://directory.example/','mode':'page'},sort_keys=True).encode()).hexdigest()}}},
 news_config={'queries':['query '+str(i) for i in range(41)],'queries_per_run':20},news_state={'last_run':STAMP,'last_summary':{'queries_attempted':20,'queries_failed':0,'errors':[]}},
 registry_state={'last_run':'2026-11-15','last_summary':{'government_records_in_region':1,'published_registry_leads':0},'seen':{'office':{}}},
 manual_state={'last_run':None,'last_week':None},manual_queue={'items':[]})

class StageHealthTests(unittest.TestCase):
 def test_review_false_green_regressions(self):
  for case in ('url','mode','missing_signature','source_summary','directory_summary','missing_attempt','old_attempt'):
   with self.subTest(case=case):
    f=fixture()
    if case=='url':f['directory_config'][0]['url']='https://new.example/'
    if case=='mode':f['directory_config'][0]['mode']='cards'
    if case=='missing_signature':del f['directory_state']['sources']['dir']['source_signature']
    if case=='source_summary':f['source_state']['last_summary'].update(success=0,failed=2)
    if case=='directory_summary':f['directory_state']['last_summary'].update(success=0,failed=1)
    if case=='missing_attempt':del f['source_state']['sources'][E]['last_attempt']
    if case=='old_attempt':
     f['source_state']['sources'][E].update(last_attempt='2026-11-16T00:00:00+00:00',last_success='2026-11-16T00:00:00+00:00')
    self.assertFalse(m.assess_all(**f)['healthy'])
  self.assertTrue(m.assess_all(**fixture())['healthy'])

 def test_archived_batch_extras_not_equated_to_active_counts(self):
  f=fixture();f['source_state']['last_summary'].update(urls=3,success=3)
  f['source_state']['sources']['https://archived.example/']={'last_attempt':STAMP,'last_success':STAMP,'last_error':None}
  self.assertTrue(m.assess_all(**f)['healthy'])
  f['source_state']['last_summary'].update(success=2,failed=1)
  self.assertFalse(m.assess_all(**f)['healthy'])
  report=m.assess_all(**f)
  self.assertEqual(report['failed_count'],0)
  for key in ('clinic_evidence','discovery_pages'):
   stage=report['stages'][key]
   self.assertEqual(stage['failed_count'],0)
   self.assertEqual(stage['declared_batch_failed_count'],1)
   self.assertEqual(stage['declared_batch_scope'],'shared_clinic_and_discovery_sources')
   self.assertTrue(any("not this stage's count" in p for p in stage['problems']))

 def test_all_automated_stages_and_manual_nonrun_are_honest(self):
  r=m.assess_all(**fixture());self.assertTrue(r['healthy']);self.assertTrue(r['automated_stages_healthy'])
  self.assertEqual(set(r['stages']),{'clinic_evidence','discovery_pages','directories','news_discovery','official_registry','professional_registry_audit'})
  manual=r['stages']['professional_registry_audit'];self.assertEqual(manual['status'],'manual_only');self.assertIsNone(manual['healthy']);self.assertFalse(manual['automatic_ingestion'])
  self.assertFalse(r['optional_ai']['required']);self.assertEqual(r['optional_ai']['status'],'not_assessed')
  self.assertEqual(r['stages']['news_discovery']['configured_queries'],41)
  self.assertEqual(r['stages']['news_discovery']['successful_count'],20)
  self.assertIn('No per-query',r['stages']['news_discovery']['limitation'])

 def test_legacy_assess_remains_evidence_only(self):
  s={'last_run':STAMP,'sources':{E:{'last_success':STAMP,'last_error':None}}};db={'clinics':[{'evidence_url':E}]}
  self.assertTrue(m.assess(db,s,NOW)['healthy'])
  self.assertFalse(m.assess(db,s,NOW+dt.timedelta(hours=37))['healthy'])
  s['sources'][E]['last_error']='403';self.assertEqual(m.assess(db,s,NOW)['failed_count'],1)
  self.assertEqual(m.assess(db,{'sources':{}},NOW)['unscanned_count'],1)

 def test_discovery_only_failure_and_overlap_not_hidden(self):
  f=fixture();f['source_state']['sources'][D]['last_error']='403';f['source_state']['sources'][D]['error_category']='blocked_access'
  r=m.assess_all(**f);self.assertFalse(r['healthy']);self.assertTrue(r['stages']['clinic_evidence']['healthy']);self.assertEqual(r['stages']['discovery_pages']['failed_count'],1)
  f['discovery_sources'].append({'url':E});r=m.assess_all(**f)
  self.assertEqual(r['stages']['discovery_pages']['overlapping_evidence_urls'],1)

 def test_partial_directory_failure_unscanned_and_stale(self):
  f=fixture();cfg=f['directory_config'];cfg.extend([{'id':'missing','name':'Missing','url':'https://missing.example','mode':'people'},{'id':'stale','name':'Stale','url':'https://stale.example','mode':'table'}])
  ds=f['directory_state'];ds['last_summary']={'sources':3,'success':1,'failed':2}
  ds['sources']['dir']['last_error']='certificate failure';ds['sources']['dir']['error_category']='tls_error'
  ds['sources']['stale']={'last_success':'2026-11-10','last_attempt':'2026-11-15','last_error':None,'entry_count':1,'entries':{'a':{}}}
  s=m.assess_all(**f)['stages']['directories']
  self.assertEqual((s['failed_count'],s['unscanned_count'],s['stale_count']),(1,1,1));self.assertFalse(s['healthy'])
  self.assertEqual(s['items'][0]['category'],'tls_error')

 def test_date_only_36h_interval_never_invents_precision(self):
  a=m.clock('2026-11-15',NOW);self.assertEqual(a['precision'],'date');self.assertEqual((a['age_hours_min'],a['age_hours_max']),(1,25));self.assertEqual(a['status'],'fresh')
  f=fixture();f['now']=NOW.replace(hour=13)
  r=m.assess_all(**f);s=r['stages']['directories'];self.assertFalse(s['healthy']);self.assertEqual(s['last_run']['status'],'freshness_uncertain');self.assertEqual(s['uncertain_count'],1)
  self.assertEqual(m.clock('2026-11-15',dt.datetime(2026,11,17,13,tzinfo=dt.timezone.utc))['status'],'stale')
  self.assertEqual(m.clock('2026-11-16T02:00:00+02:00',NOW)['age_hours_max'],1)

 def test_future_naive_malformed_clocks_fail_visible(self):
  for bad in ['2026-11-17','2026-11-16T02:00:00+00:00','2026-11-16T00:00:00','garbage',{},42]:
   with self.subTest(bad=bad):
    f=fixture();f['source_state']['sources'][E]['last_success']=bad
    r=m.assess_all(**f);self.assertFalse(r['healthy']);self.assertEqual(r['stages']['clinic_evidence']['invalid_count'],1)
  for stage,key in [('directory_state','last_run'),('news_state','last_run'),('registry_state','last_attempt')]:
   f=fixture();f[stage][key]='2027-01-01';self.assertFalse(m.assess_all(**f)['healthy'])

 def test_missing_and_malformed_required_files_never_green(self):
  for key in ['db','source_state','discovery_sources','directory_config','directory_state','news_config','news_state','registry_state']:
   for bad in [None,[],42,'broken']:
    with self.subTest(key=key,bad=bad):
     f=fixture();f[key]=bad;r=m.assess_all(**f);self.assertFalse(r['healthy']);self.assertTrue(r['problems'])

 def test_malformed_summaries_configs_and_directory_counts(self):
  for key in ['source_state','directory_state','news_state','registry_state']:
   f=fixture();f[key]['last_summary']=None;self.assertFalse(m.assess_all(**f)['healthy'])
  for delta in [{'mode':'unsupported'},{'url':'https://['},{'url':'http://directory.example/'}]:
   f=fixture();f['directory_config'][0].update(delta);self.assertFalse(m.assess_all(**f)['healthy'])
  for n in [False,-1,2]:
   f=fixture();f['directory_state']['sources']['dir']['entry_count']=n;self.assertFalse(m.assess_all(**f)['healthy'])
  f=fixture();f['source_state']['sources'][E]=[];self.assertFalse(m.assess_all(**f)['healthy'])

 def test_news_partial_zero_attempts_errors_and_truncation(self):
  f=fixture();f['news_state']['last_summary'].update(queries_failed=8,errors=[{'query':'x','error':'timeout'}]*5)
  s=m.assess_all(**f)['stages']['news_discovery'];self.assertEqual(s['status'],'degraded');self.assertEqual(s['successful_count'],12);self.assertFalse(s['error_details_complete'])
  for summary in [{'queries_attempted':0,'queries_failed':0,'errors':[]},{'queries_attempted':20,'queries_failed':21,'errors':[]},{'queries_attempted':20,'queries_failed':0,'errors':[{'error':'failure'}]}]:
   f=fixture();f['news_state']['last_summary']=summary;self.assertFalse(m.assess_all(**f)['healthy'])

 def test_registry_legacy_explicit_failure_and_preserved_old_success(self):
  f=fixture();s=m.assess_all(**f)['stages']['official_registry'];self.assertTrue(s['healthy']);self.assertEqual(s['success_clock_basis'],'legacy_completed_run')
  f['registry_state'].update(last_success=STAMP,last_attempt=STAMP,last_error=None,consecutive_failures=0)
  s=m.assess_all(**f)['stages']['official_registry'];self.assertTrue(s['healthy']);self.assertEqual(s['success_clock_basis'],'explicit_last_success')
  f['registry_state'].update(last_error='HTTPS 503',consecutive_failures=1)
  s=m.assess_all(**f)['stages']['official_registry'];self.assertFalse(s['healthy']);self.assertEqual(s['failed_count'],1);self.assertEqual(s['last_success']['status'],'fresh')
  f['registry_state']['last_error']=None;self.assertFalse(m.assess_all(**f)['healthy'])
  f=fixture();f['registry_state']['seen']={};self.assertFalse(m.assess_all(**f)['healthy'])

 def test_manual_nonrun_is_not_failure_but_malformed_metadata_visible(self):
  f=fixture();self.assertTrue(m.assess_all(**f)['healthy'])
  f['manual_state']['last_week']='2027-W01';r=m.assess_all(**f)
  self.assertFalse(r['healthy']);self.assertTrue(r['automated_stages_healthy']);self.assertEqual(r['stages']['professional_registry_audit']['status'],'manual_state_invalid')
  self.assertTrue(r['manual_warnings'])
  f=fixture();f['manual_queue']['items']=[{'review_status':'pending'}];r=m.assess_all(**f)
  self.assertTrue(r['healthy']);self.assertEqual(r['stages']['professional_registry_audit']['pending_tasks'],1)

 def test_current_catches_invalid_json_without_crashing(self):
  original=pathlib.Path.read_text
  def read(path,*args,**kwargs):
   if path.name=='directory_state.json':return 'not valid JSON'
   return original(path,*args,**kwargs)
  with patch.object(pathlib.Path,'read_text',read):r=m.current()
  self.assertFalse(r['healthy']);self.assertIn('directory_state',r['state_load_errors']);self.assertFalse(r['stages']['directories']['healthy'])

 def test_many_failures_keep_exact_counts_and_bound_issue_detail(self):
  f=fixture();urls=['https://clinic'+str(i)+'.example/patients' for i in range(80)]
  f['db']['clinics']=[{'evidence_url':u} for u in urls]
  f['source_state']['sources']={u:{'last_success':STAMP,'last_attempt':STAMP,'last_error':'Error '+('detail '*100),'error_category':'blocked_access'} for u in urls}
  f['source_state']['sources'][D]={'last_success':STAMP,'last_attempt':STAMP,'last_error':None}
  f['source_state']['last_summary']={'urls':81,'success':1,'failed':80}
  r=m.assess_all(**f)
  self.assertEqual(r['failed_count'],80);self.assertEqual(r['stages']['clinic_evidence']['failed_count'],80)
  self.assertTrue(r['detail_truncation']);self.assertFalse(r['healthy'])
  self.assertLessEqual(len(json.dumps(r,indent=2)),48000)

 def test_stale_news_success_count_does_not_claim_current_coverage(self):
  f=fixture();f['news_state']['last_run']='2026-11-01T00:00:00+00:00'
  s=m.assess_all(**f)['stages']['news_discovery']
  self.assertEqual(s['successful_count'],0)
  self.assertEqual(s['last_batch_successful_count'],20)
  self.assertEqual(s['status'],'stale')

 def test_success_after_latest_attempt_is_invalid_not_green(self):
  f=fixture();f['source_state']['sources'][E]['last_attempt']='2026-11-15T00:00:00+00:00'
  self.assertFalse(m.assess_all(**f)['stages']['clinic_evidence']['healthy'])
  f=fixture();f['registry_state'].update(last_success=STAMP,last_attempt='2026-11-15T00:00:00+00:00')
  self.assertFalse(m.assess_all(**f)['stages']['official_registry']['healthy'])

 def test_actual_state_read_only_and_reports_stage_scope(self):
  paths=list((m.ROOT/'data').glob('*.json'))
  before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
  r=m.current();self.assertEqual(r['health_scope'],'all_automated_stages_and_manual_metadata')
  self.assertIn('professional_registry_audit',r['stages']);self.assertIn('optional_ai',r)
  self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
  json.dumps(r,allow_nan=False)

if __name__=='__main__':unittest.main(verbosity=2)
