"""Opaque email protection nonce is not a changed clinic announcement."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import directory_discovery as d
SOURCE={'id':'test','name':'Providers','url':'https://example.org/contact.htm','mode':'table'}
def html(fragment='abc123', detail='Please email to request a Patient Registration Form'):
 return f'<table><tr><td>Dr. Sunil Bhatia</td><td>Saginaw Medical Centre</td><td>{detail} <a href="/cdn-cgi/l/email-protection#{fragment}">[email protected]</a></td></tr></table>'
class EmailNoiseTests(unittest.TestCase):
 def test_random_fragment_does_not_change_record_or_raise_lead(self):
  a=d.parse_candidates(html(),SOURCE);b=d.parse_candidates(html('def456'),SOURCE)
  self.assertEqual(a,b)
  self.assertEqual(a[0]['link'],SOURCE['url'])
  s={'sources':{}};q={'items':[]}
  d.process([SOURCE],{'test':html()},s,q,[],'2026-11-16');q['items'].clear()
  summary=d.process([SOURCE],{'test':html('def456')},s,q,[],'2026-11-17')
  self.assertEqual(summary['new_directory_leads'],0);self.assertEqual(q['items'],[])
 def test_real_detail_changes_still_raise_review(self):
  s={'sources':{}};q={'items':[]}
  d.process([SOURCE],{'test':html()},s,q,[],'2026-11-16');q['items'].clear()
  summary=d.process([SOURCE],{'test':html('def456','No longer accepting patients')},s,q,[],'2026-11-17')
  self.assertEqual(summary['new_directory_leads'],1)
 def test_other_navigation_fragments_remain_significant(self):
  for prefix in ['https://example.org/register#','https://other.org/cdn-cgi/l/email-protection#','https://example.org/cdn-cgi/l/email-protection?x=1#']:
   with self.subTest(prefix=prefix):
    a=d.candidate('Dr. Alpha Example','Family Medical Centre',prefix+'one',SOURCE,'directory')
    b=d.candidate('Dr. Alpha Example','Family Medical Centre',prefix+'two',SOURCE,'directory')
    self.assertNotEqual(a['content_hash'],b['content_hash'])
 def test_legacy_version_rebaselines_without_noise(self):
  s={'sources':{}};q={'items':[]}
  d.process([SOURCE],{'test':html()},s,q,[],'2026-11-16');q['items'].clear()
  s['sources']['test']['extraction_version']='directory-v3'
  result=d.process([SOURCE],{'test':html('new')},s,q,[],'2026-11-17')
  self.assertEqual(result['version_baselines'],1);self.assertEqual(q['items'],[])
if __name__=='__main__':unittest.main(verbosity=2)
