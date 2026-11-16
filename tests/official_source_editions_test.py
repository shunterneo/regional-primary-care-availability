"""Official language editions preserve provenance and cannot propose intake publication."""
import sys,pathlib,json,unittest,tempfile
from unittest.mock import patch
from types import SimpleNamespace
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import check_sources as c
import directory_discovery as d
class EditionTests(unittest.TestCase):
 def test_clinic_editions_review_only(self):
  for original,edition in c.OFFICIAL_EDITIONS.items():
   html='<html><title>Clinic</title><body>Family medical clinic accepting new patients. <a href="'+original+'">English</a></form></body></html>'
   response=SimpleNamespace(url=edition['url'],text=html,content=html.encode(),headers={'Content-Type':'text/html'})
   with patch.object(c,'request_source',return_value=response) as fetch:
    key,result=c.fetch_one((original,{}))
   fetch.assert_called_once_with(edition['url']);self.assertEqual(key,original)
   self.assertIsNone(result['error']);self.assertIsNone(result['explicit_candidate']);self.assertTrue(result['review_only'])
   self.assertEqual(result['extraction_version'],'official-language-review-v1')
   self.assertEqual(result['review_observation']['original_url'],original)
 def test_run_preserves_original_failure_and_blocks_auto_chain(self):
  original,edition=next(iter(c.OFFICIAL_EDITIONS.items()))
  body='<html><body>Family clinic accepting new patients.</body></html>'
  response=SimpleNamespace(url=edition['url'],text=body,content=body.encode(),headers={'Content-Type':'text/html'})
  with patch.object(c,'request_source',return_value=response):_,result=c.fetch_one((original,{}))
  result['explicit_candidate']={'status':'accepting'}  # Even an accidental claim cannot enter publication evidence.
  state={'sources':{original:{'hash':'old','extraction_version':'review-context-v2','last_error':'original503','http_status':503,'last_attempt':'2026-11-16T01:00:00+00:00'}}}
  queue={'items':[]}
  with tempfile.TemporaryDirectory() as t,patch.multiple(c,state=state,queue=queue,state_path=pathlib.Path(t)/'s.json',queue_path=pathlib.Path(t)/'q.json',urlmap={original:{'clinics':['c1'],'kind':'test'}},clinics=[{'id':'c1','evidence_url':original}]),patch.object(c,'fetch_one',return_value=(original,result)),patch.object(c,'first_party',return_value=True):
   c.run();record=state['sources'][original]
   self.assertFalse(record['official_first_party']);self.assertFalse(record['auto_observation'])
   self.assertEqual(record['check_method'],'official_language_edition');self.assertEqual(record['extraction_version'],'official-language-review-v1')
   self.assertEqual(record['review_observation']['original_endpoint_issue']['last_error'],'original503');self.assertEqual(queue['items'],[])
   record['last_error']='alternate503';c.run()
   self.assertEqual(state['sources'][original]['review_observation']['original_endpoint_issue']['last_error'],'original503')

 def test_unmapped_not_changed(self):
  with patch.object(c,'request_source',side_effect=ValueError('stop')) as fetch:c.fetch_one(('https://example.com/',{}))
  fetch.assert_called_once_with('https://example.com/')
 def test_edition_redirect_rejected(self):
  original,edition=next(iter(c.OFFICIAL_EDITIONS.items()))
  with patch.object(c,'request_source',return_value=SimpleNamespace(url='https://unexpected.example/')):_,r=c.fetch_one((original,{}))
  self.assertIsNotNone(r['error'])
 def test_french_directory_and_domain_boundary(self):
  source={'url':'https://www.lignesantesud-ouest.ca/listServices.aspx?id=10075','mode':'healthline'}
  html='<html><title>Cliniques de médecine familiale</title><body><form><a href="displayService.aspx?id=123">Clinique de médecine familiale Exemple</a><a href="https://lignesantesud-ouest.ca.evil.example/displayService.aspx?id=2">Bad clinic</a></form></body></html>'
  rows=d.extract_snapshot(html,source);self.assertEqual(len(rows),1)
  self.assertIn('lignesantesud-ouest.ca/displayService',rows[0]['link'])
 def test_directory_provenance(self):
  s={'url':'https://www.lignesantesud-ouest.ca/listServices.aspx?id=10075','original_url':'https://www.southwesthealthline.ca/listServices.aspx?id=10075','language':'fr'}
  prev={'last_error':'503 unavailable','error_category':'transient_http','last_attempt':'2026-11-16'}
  r=d.successful_state({},[],'2026-11-16','hash','migration',0,s,prev)
  self.assertEqual(r['observed_url'],s['url']);self.assertEqual(r['original_endpoint_issue']['last_error'],'503 unavailable')
 def test_config_preserves_originals(self):
  for s in json.loads((ROOT/'data/curated_directories.json').read_text()):
   if s.get('language')=='fr':
    self.assertIn('southwesthealthline.ca',s['original_url']);self.assertEqual(s['mode'],'healthline')
if __name__=='__main__':unittest.main()
