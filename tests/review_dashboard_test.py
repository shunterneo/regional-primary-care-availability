"""Read-only review visibility: truthful counts, safe rendering, no fact writes."""
import copy, datetime as dt, hashlib, json, pathlib, sys, tempfile, unittest
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from review_dashboard import collect, render, write_dashboard, GROUPS

class DashboardTests(unittest.TestCase):
 def make(self, d, overrides=None):
  values={'review_queue.json':{'items':[]},'discovery_queue.json':{'items':[]},'directory_queue.json':{'items':[]},'registry_audit_queue.json':{'items':[]},'source_state.json':{'sources':{}},'discovery_sources.json':[],'curated_directories.json':[],'directory_state.json':{'sources':{}},'official_registry_state.json':{'seen':{}}}
  values.update(overrides or {})
  for name,v in values.items():(d/name).write_text(json.dumps(v))

 def test_all_four_pending_queues_and_no_resolved_items(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);changes={}
   for name in ['review_queue','discovery_queue','directory_queue','registry_audit_queue']:
    changes[name+'.json']={'items':[{'id':'pending','title':name,'review_status':'pending'},{'id':'resolved','review_status':'reviewed','title':'Never show resolved'}]}
   self.make(d,changes);r=collect(d,[])
   self.assertEqual(r['total'],4);self.assertEqual(r['counts']['discovery'],2);self.assertEqual(len(r['counts_by_queue']),4)
   self.assertNotIn('Never show resolved',render(r))

 def test_unsafe_text_urls_and_private_fields_not_active_or_projected(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);self.make(d,{'review_queue.json':{'items':[{'id':'bad','review_status':'pending','title':'<img src=x onerror=alert(1)>','current_excerpt':'</script><script>alert(1)</script>','url':'javascript:alert(1)','password':'never-copy-me','patient_name':'never-copy-patient','possible_claim':'possible_accepting'}]}})
   r=collect(d,[]);h=render(r);s=BeautifulSoup(h,'html.parser')
   self.assertFalse(s.find('script'));self.assertFalse(s.find('img'));self.assertFalse(s.find('form'))
   self.assertNotIn('never-copy',h);self.assertNotIn('possible_accepting',h)
   self.assertTrue(all(a.get('href','').startswith(('https://','#','index.html')) for a in s.find_all('a')))
   self.assertIn('&lt;img',h)

 def test_malformed_and_legacy_clinic_references_do_not_break_build(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t)
   for refs in [None,42,'c1',[],['c1'],{}]:
    self.make(d,{'review_queue.json':{'items':[{'id':'x','review_status':'pending','clinic_ids':refs}]}})
    r=collect(d,[{'id':'c1','name':'One Practice'}]);self.assertEqual(r['counts']['source_change'],1)
    self.assertTrue(render(r).endswith('</html>'))
    if refs in ('c1',['c1']):self.assertIn('One Practice',r['items'][0]['title'])

 def test_missing_queue_is_visible_not_zero_success(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);self.make(d);(d/'review_queue.json').write_text('not-json');r=collect(d,[])
   self.assertIsNone(r['counts_by_queue']['review_queue.json']);self.assertTrue(r['input_errors'])
   self.assertIn('could not be loaded',render(r))

 def test_failure_snapshot_uses_only_current_sources_and_preserves_last_success(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);self.make(d,{'source_state.json':{'sources':{'https://valid.example/intake':{'last_attempt':'2026-11-16','last_success':'2026-11-15','last_error':'503','error_category':'transient_http'},'https://obsolete.example':{'last_error':'old'}}},'curated_directories.json':[{'id':'d1','name':'Example directory','url':'https://directory.example'}]})
   r=collect(d,[{'id':'c1','name':'Practice','evidence_url':'https://valid.example/intake'}]);self.assertEqual(r['counts']['failure'],2)
   h=render(r);self.assertNotIn('obsolete.example',h);self.assertIn('2026-11-15',h);self.assertIn('not evidence that intake stopped',h)

 def test_registry_observations_are_not_claimed_as_new_clinics(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);row={'id':'moh-1','name':'Program Administration','community':'London','address':'1 Main Street'}
   self.make(d,{'official_registry_state.json':{'seen':{'moh-1':{'row':row,'days':['2026-11-15']}}}})
   r=collect(d,[]);self.assertEqual(r['counts']['registry_profile'],1);h=render(r)
   self.assertIn('not a count of new or missing clinics',h);self.assertIn('administrative/specialist',h)
   self.assertEqual(collect(d,[row])['counts']['registry_profile'],0)
   possible={**row,'id':'c1','name':'Existing service at same address'}
   r=collect(d,[possible]);self.assertEqual(r['counts']['registry_profile'],1)
   self.assertIn('Same-address listings to compare',r['items'][0]['note'])
   self.assertIn('shared address alone does not establish the same practice',r['items'][0]['note'])

 def test_malformed_health_cannot_crash_or_appear_healthy(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);self.make(d);r=collect(d,[])
   for v in [['bad'],42,'bad']:
    h=render(r,{'stages':v});self.assertIn('malformed or unavailable',h)
   h=render(r,{'stages':{'bad':{'healthy':'false'}}});self.assertIn('attention needed',h)
   h=render(r,{'stages':{'bad':{'healthy':False,'status':'healthy'}}});self.assertIn('invalid',h)
   h=render(r,{'stages':{'bad':{'healthy':True,'status':'invented_status'}}});self.assertIn('unknown',h)

 def test_live_data_projection_read_only_and_full_document(self):
  before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.json')}
  clinics=json.loads((ROOT/'data/clinics.json').read_text())['clinics'];original=copy.deepcopy(clinics)
  r=collect(ROOT/'data',clinics);h=render(r)
  self.assertEqual(clinics,original);self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.json')})
  pending=lambda name:sum(x.get('review_status')=='pending' for x in json.loads((ROOT/'data'/name).read_text())['items'])
  self.assertEqual(r['counts']['source_change'],pending('review_queue.json'));self.assertEqual(r['counts']['discovery'],pending('discovery_queue.json')+pending('directory_queue.json'))
  s=BeautifulSoup(h,'html.parser');self.assertEqual(s.title.string,'Review findings | Primary Care Availability')
  self.assertTrue(s.find('main'));self.assertTrue(h.endswith('</html>'));self.assertEqual(len(s.select('details.finding')),r['total'])
  self.assertFalse(s.select('script,form,input,iframe,img'));self.assertIn('Automatic status publication is paused',s.get_text())

if __name__=='__main__':unittest.main(verbosity=2)
