"""Demonstrate source changes become proposals, never silently changed intake."""
import sys,tempfile,pathlib,json,requests
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import check_sources as c
from unittest.mock import patch
class Resp:
 def __init__(self,body):
  self.text=body;self.content=body.encode();self.headers={'Content-Type':'text/html'}
 def raise_for_status(self):pass
PUBLIC='https://example.org/public-intake'
body1='<html><nav>Menu</nav><h1>New patients</h1><p>We welcome new patient applications. Registration does not guarantee enrollment.</p></html>'
body2='<html><nav>Menu</nav><h1>New patients</h1><p>We are no longer accepting new applications. Contact reception to confirm.</p></html>'
assert c.extract(body1)!=c.extract(body2)
stamp='<p>Physician register AS OF THE DATE AND TIME NOTED BELOW 12/11/26 03:43:27 AM. Family physician practice at 123 Main Street.</p>'
assert c.extract(stamp)==c.extract(stamp.replace('03:43:27','03:55:20'))
assert c.extract(stamp)!=c.extract(stamp.replace('123 Main Street','125 Main Street'))
with tempfile.TemporaryDirectory() as temp:
 t=pathlib.Path(temp); c.state_path=t/'state.json';c.queue_path=t/'queue.json'; c.state={'version':1,'sources':{}};c.queue={'version':1,'items':[]};c.urlmap={PUBLIC:{'clinics':['c001'],'kind':'intake evidence'}}
 with patch.object(c.requests,'get',return_value=Resp(body1)):
  c.run()
 assert len(c.queue['items'])==0,'first fetch should establish baseline without false alert'
 with patch.object(c.requests,'get',return_value=Resp(body2)):
  c.run()
 assert len(c.queue['items'])==1
 assert c.queue['items'][0]['review_status']=='pending'
 assert c.queue['items'][0]['clinic_ids']==['c001']
 with patch.object(c.requests,'get',side_effect=requests.Timeout('simulated timeout')):
  c.run()
 assert len(c.queue['items'])==1,'HTTP outage must not create false closure'
 assert c.state['sources'][PUBLIC]['hash'],'last known good hash preserved after outage'
 before=json.loads((pathlib.Path(__file__).resolve().parents[1]/'data'/'clinics.json').read_text())
 assert before['clinics'][0]['id']=='c001','fixture checks the unchanged published source database'
 print('PASS: first scan baselines, changed intake creates one review proposal, timeout does not create a closure or alter status')
