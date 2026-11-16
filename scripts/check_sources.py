#!/usr/bin/env python3
"""Check public clinic/source pages for meaningful content changes.

SAFETY: Never automatically alter a clinic's intake status. This script creates
review proposals from changes and records source scan health; it does not make
unverified claims about new openings or closures.
"""
from __future__ import annotations
import concurrent.futures, datetime, hashlib, html, json, re, pathlib, sys, time
import requests, io
from pypdf import PdfReader
from bs4 import BeautifulSoup
from common import ROOT,load_data,is_url
from intake_evidence import classify, REVIEW_CLASSIFIER_VERSION
from auto_evidence import decisive_statement, observe, first_party, publication_candidate, scope_fingerprint
from source_observation import REVIEW_VERSION, document_context, normalize_text
DATA=ROOT/'data';state_path=DATA/'source_state.json';queue_path=DATA/'review_queue.json'
state=json.loads(state_path.read_text());queue=json.loads(queue_path.read_text());clinics=load_data()['clinics']
extra=json.loads((DATA/'discovery_sources.json').read_text())
urlmap={}
for c in clinics:
    url=c.get('evidence_url')
    if is_url(url): urlmap.setdefault(url,{'clinics':[], 'kind':'intake evidence'})['clinics'].append(c['id'])
for source in extra:
    url=source['url']
    if is_url(url):urlmap.setdefault(url,{'clinics':[],'kind':'clinic discovery'})

USER_AGENT='RegionalPrimaryCareAvailabilityMonitor/1.0 (public-source change check; no patient data)'
TERMS=re.compile(r'accept(?:ing|ance)?|new patients?|not accepting|register|registration|intake|enrol|attach|capacity|wait ?list|physician|practitioner|family doctor|clos(?:ed|ure|ing)|retir|relocat',re.I)

def extract(text):
    bs=BeautifulSoup(text,'html.parser')
    for bad in bs(['script','style','noscript','svg','header','footer','nav','form']):bad.decompose()
    # Collapse whitespace and use only meaningful content matching intake vocabulary.
    raw=' '.join(bs.stripped_strings)
    return extract_plain(raw)

def extract_plain(raw):
    raw=normalize_text(raw)
    # Sentence boundaries are imperfect but deterministic; enough for an evidence-change alert.
    parts=re.split(r'(?<=[.!?])\s+|(?<=\n)\s*',raw)
    relevant=[p.strip()[:400] for p in parts if TERMS.search(p) and len(p.strip())>12]
    if not relevant: relevant=[raw[:1200]]
    return '\n'.join(relevant)[:9000]

class SourceContentError(ValueError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category=category

def page_problem(text):
    """Distinguish access challenges from empty/JavaScript shells for review.

    Never solve a challenge or treat script-rendered content as intake evidence.
    """
    bs=BeautifulSoup(text,'html.parser')
    title=' '.join(bs.title.stripped_strings) if bs.title else ''
    noscript=' '.join(n.get_text(' ',strip=True) for n in bs.find_all('noscript'))
    has_script=bool(bs.find('script',src=True))
    for node in bs(['script','style','noscript','template','svg','head']):node.decompose()
    plain=' '.join(bs.stripped_strings).strip()
    challenge=r'(?:just a moment[.!…]*|access denied|attention required!?|verify (?:you are|that you are) human|checking your browser)'
    if re.fullmatch(challenge,title.strip(),re.I) or (len(plain)<500 and re.match(challenge,plain,re.I)):
        return ('blocked_page','Access challenge or denial; manual review required, no bypass attempted')
    if len(plain)<500 and re.match(r'sign in to continue',plain,re.I):
        return ('login_required','Sign-in required; no authentication attempted')
    js=r'(?:enable|requires?|need).*javascript|javascript.*(?:required|enabled)'
    if len(plain)<500 and (re.search(js,plain+' '+noscript,re.I) or (len(plain)<12 and has_script)):
        return ('render_required','JavaScript page shell; readable source needs a separate rendered-page review')
    if len(plain)<12:return ('empty_content','Empty response body; no readable source text')
    return None

def usable_page(text):
    return page_problem(text) is None

def error_category(exc):
    if isinstance(exc,SourceContentError):return exc.category
    if isinstance(exc,requests.exceptions.SSLError):return 'tls_error'
    if isinstance(exc,(requests.Timeout,requests.ConnectionError)):return 'transient_network'
    if isinstance(exc,requests.HTTPError):
        code=getattr(exc.response,'status_code',None)
        if code in (401,403):return 'blocked_access'
        if code == 429 or code in (500,502,503,504):return 'transient_http'
        return 'http_error'
    if 'challenge or login' in str(exc):return 'blocked_page'
    return 'unsupported_or_invalid_content'

def request_source(url):
    # Retry only transient failures. Never evade access controls or disable TLS.
    for attempt in range(3):
        try:
            res=requests.get(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html, application/pdf'},timeout=(7,16),allow_redirects=True)
            res.raise_for_status()
            return res
        except Exception as exc:
            if attempt == 2 or error_category(exc) not in ('transient_network','transient_http'):raise
            # Respect long server retry windows by leaving this source for a later run.
            retry_after=getattr(getattr(exc,'response',None),'headers',{}).get('Retry-After','')
            if retry_after:
                try:
                    if float(retry_after)>10:raise exc
                except ValueError:raise exc
            time.sleep(max(2**attempt,float(retry_after or 0)))

def fetch_one(pair):
    url, meta=pair
    try:
        res=request_source(url)
        if len(res.content)>4_000_000:raise ValueError('Page too large')
        content_type=res.headers.get('Content-Type','text/html').lower()
        is_pdf='application/pdf' in content_type
        if is_pdf:
            reader=PdfReader(io.BytesIO(res.content))
            if reader.is_encrypted:raise ValueError('Encrypted PDF')
            if len(reader.pages)>100:raise ValueError('PDF too long')
            context=document_context(' '.join(page.extract_text() or '' for page in reader.pages),getattr(res,'url',url),'pdf')
            body=extract_plain(context['text'])
        elif 'html' in content_type:
            problem=page_problem(res.text)
            if problem:raise SourceContentError(*problem)
            context=document_context(res.text,getattr(res,'url',url),'html')
            body=extract_plain(context['text'])
        else:raise ValueError('Response is not HTML or PDF')
        if not body.strip():raise ValueError('No matching text')
        return url,{'hash':context['hash'],'extraction_version':REVIEW_VERSION,
          'review_observation':{**{k:v for k,v in context.items() if k!='text'},
            'response_sha256':hashlib.sha256(res.content).hexdigest(),
            'response_bytes':len(res.content),'rendered':False},
          'error':None,'excerpt':body[:1400],'assessment':classify(body),'final_url':getattr(res,'url',url), 'explicit_candidate':None if is_pdf else publication_candidate(res.text), 'format':'pdf' if is_pdf else 'html'}
    except Exception as exc:
        return url,{'hash':None,'error':str(exc)[:800], 'error_category':error_category(exc), 'http_status':getattr(getattr(exc,'response',None),'status_code',None)}

def run():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    items=list(urlmap.items())
    changed=0;failed=0;baseline=0;ok=0;version_baselines=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for url,result in pool.map(fetch_one,items):
            prev=state['sources'].get(url,{})
            if result['error']:
                failed+=1
                state['sources'][url]={**prev,'last_attempt':now,'last_error':result['error'],'error_category':result['error_category'],'http_status':result.get('http_status'),'auto_observation':{}}
                continue
            ok+=1
            newhash=result['hash'];oldhash=prev.get('hash')
            same_version=prev.get('extraction_version')==REVIEW_VERSION
            owners=urlmap[url]['clinics']
            verified=bool(len(owners)==1 and first_party(next(c for c in clinics if c['id']==owners[0]),url,owners,result['final_url']))
            prior_obs=prev.get('auto_observation',{}) if verified else {}
            # A failed, ambiguous or redirected page breaks the consecutive evidence chain.
            scope_hash=scope_fingerprint(next(c for c in clinics if c['id']==owners[0])) if verified else None
            observation=observe(prior_obs,result['explicit_candidate'] if verified else None,now,scope_hash=scope_hash)
            migrated={}
            if oldhash and not same_version:
                migrated['previous_extraction']={'version':prev.get('extraction_version','legacy-excerpt-v1'),
                  'hash':oldhash,'last_success':prev.get('last_success')}
            state['sources'][url]={**prev,**migrated,'hash':newhash,'extraction_version':REVIEW_VERSION,
              'review_observation':{**result['review_observation'],'observed_at':now},'excerpt':result['excerpt'][:1400],
              'possible_claim':result['assessment']['classification'],'assessment_version':REVIEW_CLASSIFIER_VERSION,'last_attempt':now,'last_success':now,
              'last_error':None,'error_category':None,'http_status':None,'format':result['format'],'final_url':result['final_url'],'official_first_party':verified,'auto_observation':observation}
            if not oldhash:
                baseline+=1;continue
            # An extraction upgrade is a new baseline, not a real source change.
            # Preserve the preceding version/hash rather than comparing unlike
            # observations or inventing an intake-change alert.
            if not same_version:
                version_baselines+=1;continue
            if oldhash!=newhash:
                changed+=1
                queue['items'].append({
                  # Returning to an earlier content hash is a new transition,
                  # even if a review item for that content was already resolved.
                  # Unchanged repeated scans are deduplicated by the state hash.
                  'id':hashlib.sha256(json.dumps([url,oldhash,newhash,now,len(queue['items'])]).encode()).hexdigest()[:18],
                  'detected_at':now,'url':url,'clinic_ids':urlmap[url]['clinics'],
                  'source_kind':urlmap[url]['kind'],'old_hash':oldhash,'new_hash':newhash,
                  'extraction_version':REVIEW_VERSION,
                  'assessment_version':REVIEW_CLASSIFIER_VERSION,
                  'review_status':'pending',
                  'prior_excerpt':prev.get('excerpt','')[:900],
                  'current_excerpt':result['excerpt'][:1400],
                  'possible_claim':result['assessment']['classification'],
                  'matched_excerpts':result['assessment']['excerpts'],
                  'note':'Raw public source content or its links changed. Text may be hidden, conditional or dynamically replaced. Verify the visible clinic-specific source; do not infer opening or closure automatically.'})
    state['last_run']=now;state['last_summary']={'urls':len(items),'success':ok,'failed':failed,'new_baselines':baseline,'extraction_version_baselines':version_baselines,'extraction_version':REVIEW_VERSION,'source_changes_queued':changed}
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    queue_path.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Source monitor:',state['last_summary'])
    if failed==len(items):
        print('WARNING: All source checks failed. Previous statuses are preserved; do not treat this as closures.',file=sys.stderr)
    return 0

if __name__=='__main__':sys.exit(run())
