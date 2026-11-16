"""Offline directory health/delta regressions. No network or clinic-data writes."""
import copy,json,pathlib,sys,unittest
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import requests
import directory_discovery as d

PAGE={'id':'page','name':'Clinic resource notice','url':'https://example.org/resource','mode':'page'}
NEWS={'id':'news','name':'Municipal news','url':'https://example.org/news/','mode':'news'}
TABLE={'id':'table','name':'Provider directory','url':'https://example.org/providers','mode':'table'}
def table(name='Dr. Alpha Example',detail='Family Medical Centre'):
 return f'<table><tr><td>{name}</td><td>{detail}</td><td>1 Main Street</td></tr></table>'
def news(title='New family physician opens a clinic'):
 return f'<html><title>News | City</title><h1>News</h1><a href="/news/example">{title}</a></html>'
def state_for(source,html):
 s={'sources':{}};q={'items':[]};d.process([source],{source['id']:html},s,q,[],'2026-11-15');return s,q

class DirectoryHealthTests(unittest.TestCase):
 def test_healthline_domain_boundary_keeps_legitimate_root_not_near_matches(self):
  src={'id':'healthline','name':'Healthline directory','url':'https://www.southwesthealthline.ca/listServices.aspx?id=10075','mode':'healthline'}
  for host,expected in [('southwesthealthline.ca',1),('www.southwesthealthline.ca',1),
                        ('healthline.ca',1),('www.healthline.ca',1),
                        ('evilhealthline.ca',0),('evilsouthwesthealthline.ca',0),
                        ('southwesthealthline.ca.evil.example',0)]:
   with self.subTest(host=host):
    html=f'<a href="https://{host}/displayService.aspx?id=1">Example Family Medical Centre</a>'
    self.assertEqual(len(d.parse_candidates(html,src)),expected)

 def test_recurring_page_transition_alerts_after_resolution_and_same_day(self):
  a='<p>Clinic notice A.</p>';b='<p>Clinic notice B.</p>'
  s,q=state_for(PAGE,a)
  for html in [b,a,b]:
   summary=d.process([PAGE],{'page':html},s,q,[],'2026-11-16')
   self.assertEqual(summary['new_directory_leads'],1)
   q['items'][-1]['review_status']='resolved'
   before=len(q['items'])
   self.assertEqual(d.process([PAGE],{'page':html},s,q,[],'2026-11-16')['new_directory_leads'],0)
   self.assertEqual(len(q['items']),before)
  self.assertEqual(len(q['items']),3)
  self.assertEqual(len({row['id'] for row in q['items']}),3)
  self.assertEqual([row['event_sequence'] for row in q['items']],[1,2,3])
  for row in q['items']:
   self.assertEqual(row['extraction_version'],d.EXTRACTION_VERSION)
   self.assertEqual(row['source_signature'],d.source_signature(PAGE))
   self.assertEqual(row['source_url'],PAGE['url'])
   self.assertEqual(row['source_mode'],PAGE['mode'])

 def test_repeated_removal_after_reappearance_has_distinct_events(self):
  a=table('Dr. Alpha Example');b=table('Dr. Beta Example')
  s,q=state_for(TABLE,a+b)
  for html in [b,a+b,b]:
   summary=d.process([TABLE],{'table':html},s,q,[],'2026-11-16')
   for row in q['items']:row['review_status']='resolved'
   self.assertEqual(d.process([TABLE],{'table':html},s,q,[],'2026-11-16')['listing_removals_to_review'],0)
  removed=[row for row in q['items'] if 'removed or renamed' in row.get('proposed_action','')]
  self.assertEqual(len(removed),2)
  self.assertNotEqual(removed[0]['id'],removed[1]['id'])
  self.assertEqual([row['event_sequence'] for row in removed],[1,3])
  self.assertTrue(all(row['intake_status']=='unconfirmed' for row in removed))

 def test_page_link_targets_and_base_resolution_are_hashed_without_fetch(self):
  a='<base href="https://example.org/old/"><p>Clinic registration information.</p><a href="intake">Registration</a>'
  b=a.replace('/old/','/new/')
  s,q=state_for(PAGE,a)
  with patch.object(d.requests,'get') as get:
   summary=d.process([PAGE],{'page':b},s,q,[],'2026-11-16')
   get.assert_not_called()
  self.assertEqual(summary['new_directory_leads'],1)
  self.assertTrue(q['items'][-1]['preview_unchanged'])
  # An absolute target resolving to the same URL is semantically unchanged.
  equivalent=b.replace('href="intake"','href="https://example.org/new/intake"')
  self.assertEqual(d.process([PAGE],{'page':equivalent},s,q,[],'2026-11-17')['new_directory_leads'],0)
  changed=equivalent.replace('/new/intake','/new/closed')
  self.assertEqual(d.process([PAGE],{'page':changed},s,q,[],'2026-11-17')['new_directory_leads'],1)

 def test_page_link_bound_preserves_baseline_without_truncation(self):
  s,q=state_for(PAGE,'<p>Public clinic information.</p>');old=copy.deepcopy(s['sources']['page'])
  html='<p>Public clinic information.</p>'+''.join(f'<a href="/public/{i}">Resource</a>' for i in range(d.MAX_PAGE_LINKS+1))
  summary=d.process([PAGE],{'page':html},s,q,[],'2026-11-16')
  self.assertEqual(summary['failed'],1)
  self.assertEqual(s['sources']['page']['error_category'],'extraction_limit')
  self.assertEqual(s['sources']['page']['entries'],old['entries'])
  self.assertEqual(q['items'],[])

 def test_complete_page_hash_not_preview_drives_change(self):
  prefix='<h1>Primary care information</h1><p>'+'Welcome to the community. '*30+'</p>'
  a=prefix+'<p>Family practice registration is open.</p>'
  b=prefix+'<p>Family practice registration has stopped.</p>'
  s,q=state_for(PAGE,a);old=copy.deepcopy(s)
  summary=d.process([PAGE],{'page':b},s,q,[],'2026-11-16')
  self.assertEqual(summary['new_directory_leads'],1)
  self.assertEqual(q['items'][0]['prior_excerpt'],q['items'][0]['current_excerpt'])
  self.assertTrue(q['items'][0]['preview_unchanged'])
  self.assertNotEqual(s['sources']['page']['fingerprint'],old['sources']['page']['fingerprint'])
  self.assertNotEqual(q['items'][0]['prior_content_hash'],q['items'][0]['current_content_hash'])
  self.assertEqual(q['items'][0]['intake_status'],'unconfirmed')
  self.assertLessEqual(len(q['items'][0]['current_excerpt']),440)
  self.assertEqual(d.process([PAGE],{'page':b},s,q,[],'2026-11-17')['new_directory_leads'],0)

 def test_provider_detail_after_preview_and_fifth_cell_is_hashed(self):
  a=table(detail='Family Medical Centre '+('Public information '*40))
  b=a.replace('</tr>','<td>More details</td><td>More details</td><td>Registration stopped</td></tr>')
  s,q=state_for(TABLE,a);q['items']=[]
  summary=d.process([TABLE],{'table':b},s,q,[],'2026-11-16')
  self.assertEqual(summary['new_directory_leads'],1)
  self.assertTrue(q['items'][0]['preview_unchanged'])

 def test_valid_zero_news_success_not_removal(self):
  s,q=state_for(NEWS,news());before=len(q['items'])
  summary=d.process([NEWS],{'news':news('Remembrance Day Ceremony')},s,q,[],'2026-11-16')
  self.assertEqual((summary['success'],summary['failed'],summary['zero_result_news']),(1,0,1))
  self.assertEqual(summary['listing_removals_to_review'],0)
  self.assertEqual(len(q['items']),before)
  self.assertEqual(s['sources']['news']['last_success'],'2026-11-16')
  self.assertEqual(s['sources']['news']['entries'],{})
  # The item reappears after cycling out: existing queue identity suppresses a duplicate.
  self.assertEqual(d.process([NEWS],{'news':news()},s,q,[],'2026-11-17')['new_directory_leads'],0)
  self.assertEqual(d.process([NEWS],{'news':'<h1>News</h1><p>No articles available.</p>'},s,q,[],'2026-11-18')['success'],1)

 def test_news_window_expiry_never_listing_removal_even_with_other_news(self):
  s,q=state_for(NEWS,news());n=len(q['items'])
  changed=news('New nurse practitioner joins a family practice').replace('/news/example','/news/second')
  summary=d.process([NEWS],{'news':changed},s,q,[],'2026-11-16')
  self.assertEqual(summary['new_directory_leads'],1)
  self.assertEqual(summary['listing_removals_to_review'],0)
  self.assertEqual(len(q['items']),n+1)

 def test_blocked_shell_empty_login_schema_preserve_state(self):
  cases=[('<title>Just a moment...</title><p>Verify you are human</p>','blocked_page'),
         ('<title>Access denied</title><p>'+('Error '*150)+'</p>','blocked_page'),
         ('<h1>Sign in to continue</h1>','login_required'),
         ('<div id="root"></div><script src="/app.js"></script>','render_required'),
         ('<noscript>Please enable JavaScript</noscript>','render_required'),
         ('<html></html>','empty_content'),
         ('<title>Page not found</title><p>Try the home page.</p>','error_page'),
         ('<p>The directory layout has changed.</p>','extraction_schema')]
  for html,category in cases:
   with self.subTest(category=category):
    s,q=state_for(TABLE,table());prev=copy.deepcopy(s['sources']['table']);oldq=copy.deepcopy(q)
    out=d.process([TABLE],{'table':html},s,q,[],'2026-11-16');now=s['sources']['table']
    self.assertEqual(out['failed'],1);self.assertEqual(now['error_category'],category)
    for key in ['entries','last_success','fingerprint','extraction_version','source_signature']:
     self.assertEqual(now[key],prev[key])
    self.assertEqual(q,oldq)
  s,q=state_for(NEWS,news())
  self.assertEqual(d.process([NEWS],{'news':'<p>Unrelated landing document.</p>'},s,q,[],'2026-11-16')['failed'],1)

 def test_version_and_source_changes_establish_silent_baseline(self):
  for change in ('legacy','new_version','new_url','new_mode'):
   with self.subTest(change=change):
    s,q=state_for(TABLE,table());source=copy.deepcopy(TABLE)
    if change=='legacy':s['sources']['table'].pop('extraction_version');s['sources']['table'].pop('source_signature')
    elif change=='new_version':s['sources']['table']['extraction_version']='old-version'
    elif change=='new_url':source['url']='https://example.org/new-providers'
    else:source['mode']='people'
    oldq=copy.deepcopy(q)
    html=table('Dr. Beta Example') if change!='new_mode' else '<p>Dr. Beta Example</p>'
    summary=d.process([source],{'table':html},s,q,[],'2026-11-16')
    self.assertEqual((summary['baselines'],summary['version_baselines']),(1,1))
    self.assertEqual(summary['listing_removals_to_review'],0);self.assertEqual(q,oldq)
    self.assertEqual(s['sources']['table']['extraction_version'],d.EXTRACTION_VERSION)
    # A real subsequent provider-list delta remains reviewable.
    html2=table('Dr. Gamma Example') if change!='new_mode' else '<p>Dr. Gamma Example</p>'
    summary=d.process([source],{'table':html2},s,q,[],'2026-11-17')
    self.assertEqual(summary['listing_removals_to_review'],1)

 def test_partial_limit_and_invalid_schema_preserve_previous_entries(self):
  s,q=state_for(TABLE,table());prev=copy.deepcopy(s['sources']['table']);oldq=copy.deepcopy(q)
  html='<table>'+''.join(f'<tr><td>Dr. Test Person{i}</td><td>Family practice</td></tr>' for i in range(d.MAX_ENTRIES+1))+'</table>'
  summary=d.process([TABLE],{'table':html},s,q,[],'2026-11-16')
  self.assertEqual(summary['failed'],1);self.assertEqual(s['sources']['table']['error_category'],'extraction_limit')
  self.assertEqual(s['sources']['table']['entries'],prev['entries']);self.assertEqual(q,oldq)
  for bad in [[{'key':'bad'}],None]:
   with patch.object(d,'parse_candidates',return_value=bad):
    summary=d.process([TABLE],{'table':table()},s,q,[],'2026-11-17')
   self.assertEqual(summary['failed'],1);self.assertEqual(q,oldq)

 def test_one_source_failure_does_not_erase_or_stop_other_source(self):
  s,q=state_for(TABLE,table());prev=copy.deepcopy(s['sources']['table'])
  summary=d.process([TABLE,PAGE],{'table':None,'page':'<p>A readable clinic resource notice.</p>'},s,q,[],'2026-11-16',
                    fetch_errors={'table':{'category':'tls_error','error':'certificate verify failed: unable to get local issuer certificate'}})
  self.assertEqual((summary['failed'],summary['success']),(1,1))
  self.assertIn('local issuer certificate',s['sources']['table']['last_error'])
  self.assertEqual(s['sources']['table']['entries'],prev['entries'])

 def test_whitespace_only_change_does_not_queue(self):
  s,q=state_for(PAGE,'<p>Public clinic information.</p>')
  summary=d.process([PAGE],{'page':'<p> Public   clinic information. </p>'},s,q,[],'2026-11-16')
  self.assertEqual(summary['new_directory_leads'],0)

 def test_fetch_keeps_tls_and_rejects_http_redirect(self):
  r=MagicMock();r.url='http://example.org/resource';r.headers={'Content-Type':'text/html'};r.content=b'<p>Public information.</p>';r.text=r.content.decode()
  with patch.object(d.requests,'get',return_value=r) as get:
   with self.assertRaises(ValueError):d.fetch_html(PAGE)
   self.assertNotEqual(get.call_args.kwargs.get('verify'),False)

 def test_run_writes_only_directory_state_and_queue_with_clinics_unchanged(self):
  source=copy.deepcopy(PAGE);clinic_data={'clinics':[{'id':'c1','name':'Example Clinic','status':'unknown'}]}
  conf,state,queue,clinics=[MagicMock() for _ in range(4)]
  conf.read_text.return_value=json.dumps([source]);state.read_text.return_value=json.dumps({'sources':{}})
  queue.read_text.return_value=json.dumps({'items':[]});clinics.read_text.return_value=json.dumps(clinic_data)
  with patch.multiple(d,CONF=conf,STATE=state,QUEUE=queue,CLINICS=clinics),patch.object(d,'fetch_html',return_value='<p>Public clinic information.</p>'):
   self.assertEqual(d.run(),0)
  self.assertEqual(state.write_text.call_count,1);self.assertEqual(queue.write_text.call_count,1)
  conf.write_text.assert_not_called();clinics.write_text.assert_not_called()
  result=json.loads(state.write_text.call_args.args[0]);self.assertEqual(result['last_summary']['success'],1)

if __name__=='__main__':unittest.main(verbosity=2)
