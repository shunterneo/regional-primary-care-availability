"""Historical reconciliation is version-bound, read-only, and fail-closed."""
import ast, pathlib, datetime as dt, copy, json, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Test pure helper without requests/BeautifulSoup dependencies.
mod=ast.parse((ROOT/'scripts/review_dashboard.py').read_text())
fn=next(n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name=='reviewed_registry_identity')
ns={'dt':dt,'url':lambda u:isinstance(u,str) and u.startswith('https://')}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'helper','exec'),ns)
check=ns['reviewed_registry_identity']
class Tests(unittest.TestCase):
 def setUp(self):
  self.reviews=json.loads((ROOT/'data/registry_reconciliation.json').read_text())['reviews'];self.clinics=json.loads((ROOT/'data/clinics.json').read_text())['clinics'];self.rows=[v['row'] for v in json.loads((ROOT/'data/official_registry_state.json').read_text())['seen'].values()];self.now=dt.datetime(2026,11,18,tzinfo=dt.timezone.utc)
 def test_all_prior_identities_still_match(self):
  self.assertEqual(len(self.rows),40)
  for row in self.rows:self.assertIsNotNone(check(row,self.clinics,self.reviews,self.now))
 def test_changed_source_reopens(self):
  for key in ('id','name','community','address','clinic_type','registry_id'):
   row=copy.deepcopy(self.rows[0]);row[key]+=' changed';self.assertIsNone(check(row,self.clinics,self.reviews,self.now))
 def test_changed_clinic_reopens(self):
  row=next(r for r in self.rows if self.reviews[r['id']].get('clinic_identity'))
  for key in ('id','name','address','community'):
   clinics=copy.deepcopy(self.clinics);cid=self.reviews[row['id']]['clinic_identity']['id'];next(c for c in clinics if c['id']==cid)[key]+='changed';self.assertIsNone(check(row,clinics,self.reviews,self.now))
 def test_malformed_or_unapproved_stays_pending(self):
  row=self.rows[0]
  for field,value in [('reviewed_on','bad'),('reviewed_on','2099-01-01'),('disposition','approved'),('sources',[]),('sources',['javascript:bad']),('finding','')]:
   reviews=copy.deepcopy(self.reviews);reviews[row['id']][field]=value;self.assertIsNone(check(row,self.clinics,reviews,self.now))
 def test_no_mutation(self):
  old=copy.deepcopy((self.rows,self.clinics,self.reviews))
  for row in self.rows:check(row,self.clinics,self.reviews,self.now)
  self.assertEqual(old,(self.rows,self.clinics,self.reviews))
if __name__=='__main__':unittest.main()
