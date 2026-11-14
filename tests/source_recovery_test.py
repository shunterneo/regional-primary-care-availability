"""Offline fetch recovery tests: no access bypass or unsupported intake publication."""
import sys,pathlib,requests,io
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import check_sources as c
class Resp:
 def __init__(self,code=200):
  self.status_code=code;self.headers={'Content-Type':'text/html'};self.text='<html><p>Clinic registration information here.</p></html>';self.content=self.text.encode()
 def raise_for_status(self):
  if self.status_code>=400:raise requests.HTTPError(str(self.status_code),response=self)
with patch.object(c.requests,'get',side_effect=[requests.Timeout('timeout'),Resp()]) as get,patch.object(c.time,'sleep'):
 assert c.fetch_one(('https://example.org',{}))[1]['error'] is None;assert get.call_count==2
for code in [403,404]:
 with patch.object(c.requests,'get',return_value=Resp(code)) as get,patch.object(c.time,'sleep'):
  result=c.fetch_one(('https://example.org',{}))[1];assert result['error'];assert get.call_count==1
with patch.object(c.requests,'get',side_effect=requests.exceptions.SSLError('bad certificate')) as get:
 assert c.fetch_one(('https://example.org',{}))[1]['error_category']=='tls_error';assert get.call_count==1
r=Resp(429);r.headers['Retry-After']='60'
with patch.object(c.requests,'get',return_value=r) as get,patch.object(c.time,'sleep'):
 assert c.fetch_one(('https://example.org',{}))[1]['error'];assert get.call_count==1
r=Resp();r.headers={'Content-Type':'application/pdf'};r.content=b'%PDF-fixture'
class Page:
 def extract_text(self):return 'We are accepting new patients. Contact the clinic.'
class Reader:
 is_encrypted=False;pages=[Page()]
with patch.object(c.requests,'get',return_value=r),patch.object(c,'PdfReader',return_value=Reader()):
 result=c.fetch_one(('https://example.org/file.pdf',{}))[1]
 assert result['format']=='pdf' and result['error'] is None
 assert result['explicit_candidate'] is None,'PDF observations must remain review-only'
print('PASS: bounded transient retry, permanent/TLS no retry, Retry-After respected, PDF review only')

# Distinguish inaccessible pages from render-only shells without bypassing either.
for body,category in [
 ('<title>Just a moment...</title><script src="challenge.js"></script>','blocked_page'),
 ('<div id="root"></div><script src="app.js"></script>','render_required'),
 ('<noscript>Please enable JavaScript</noscript>','render_required'),
 ('<p>Sign in to continue</p>','login_required'),
 ('<html></html>','empty_content')]:
 r=Resp();r.text=body;r.content=body.encode()
 with patch.object(c.requests,'get',return_value=r) as get:
  result=c.fetch_one(('https://example.org',{}))[1]
  assert result['error_category']==category,(category,result)
  assert result['hash'] is None and get.call_count==1
assert c.usable_page('<h1>Patient information</h1><p>If you need support, please contact our clinic.</p>')
assert c.usable_page('<p>Our clinic has access denied parking areas for safety. Registration remains available.</p>')
print('PASS: challenges, login, JS shells and empty bodies diagnosed separately; no evidence or retry from inaccessible content')
