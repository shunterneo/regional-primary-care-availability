"""Bounded normal retries only, no access/TLS bypass or false evidence."""
import pathlib,sys,unittest,datetime as dt
from unittest.mock import patch
import requests
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import directory_discovery as d
import check_sources as c
URL='https://example.org/directory'
SOURCE={'url':URL,'id':'fixture','name':'Fixture','mode':'page'}
class Response:
 def __init__(self,code=200,retry=None):
  self.url=URL;self.status_code=code;self.text='<p>Public primary care resource information.</p>';self.content=self.text.encode();self.headers={'Content-Type':'text/html'}
  if retry is not None:self.headers['Retry-After']=retry
 def raise_for_status(self):
  if self.status_code>=400:raise requests.HTTPError(str(self.status_code),response=self)
class DirectoryRetryTests(unittest.TestCase):
 def test_timeout_and_503_one_retry_can_recover(self):
  for error in [requests.Timeout('temporary'),Response(503)]:
   with patch.object(d.requests,'get',side_effect=[error,Response()]) as get,patch.object(d.time,'sleep') as sleep:
    self.assertIn('primary care',d.fetch_html(SOURCE));self.assertEqual(get.call_count,2);sleep.assert_called_once()
    self.assertTrue(all(x.kwargs.get('verify') is not False for x in get.call_args_list))
 def test_at_most_two_attempts(self):
  with patch.object(d.requests,'get',side_effect=requests.Timeout('still down')) as get,patch.object(d.time,'sleep'):
   with self.assertRaises(requests.Timeout):d.fetch_html(SOURCE)
   self.assertEqual(get.call_count,2)
 def test_permanent_and_tls_failures_never_retry(self):
  for error in [Response(401),Response(403),Response(404),requests.exceptions.SSLError('issuer unavailable')]:
   with patch.object(d.requests,'get',side_effect=[error]) as get,patch.object(d.time,'sleep') as sleep:
    with self.assertRaises(requests.RequestException):d.fetch_html(SOURCE)
    self.assertEqual(get.call_count,1);sleep.assert_not_called()
 def test_short_retry_after_obeyed_long_or_invalid_not_retried(self):
  with patch.object(d.requests,'get',side_effect=[Response(429,'4'),Response()]) as get,patch.object(d.time,'sleep') as sleep:
   d.fetch_html(SOURCE);self.assertEqual(get.call_count,2);sleep.assert_called_once_with(4.0)
  for after in ['60','NaN','inf','-1','unparseable','Tue, 31 Dec 2030 00:00:00 GMT']:
   with patch.object(d.requests,'get',return_value=Response(429,after)) as get,patch.object(d.time,'sleep') as sleep:
    with self.assertRaises(requests.HTTPError):d.fetch_html(SOURCE)
    self.assertEqual(get.call_count,1);sleep.assert_not_called()
 def test_actual_211_shape_is_access_challenge_not_empty_or_intake(self):
  body='<title>Verification</title><script>verifyBrowser();</script><body></body>'
  self.assertEqual(c.page_problem(body)[0],'blocked_page')
  with self.assertRaises(d.ExtractionError) as cm:d.extract_snapshot(body,SOURCE)
  self.assertEqual(cm.exception.category,'blocked_page')
  self.assertIsNone(c.page_problem('<title>Verification</title><p>Clinic verification information describes our public registration process.</p>'))
if __name__=='__main__':unittest.main(verbosity=2)
