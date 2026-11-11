#!/usr/bin/env python3
"""Check public clinic/source pages for meaningful content changes.

SAFETY: Never automatically alter a clinic's intake status. This script creates
review proposals from changes and records source scan health; it does not make
unverified claims about new openings or closures.
"""
from __future__ import annotations
import concurrent.futures, datetime, hashlib, html, json, re, pathlib, sys, time
import requests
from bs4 import BeautifulSoup
from common import ROOT,load_data,is_url
from intake_evidence import classify
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
TERMS=re.compile(r'accept(?:ing|ance)?|new patients?|not accepting|register|registration|intake|enrol|attach|capacity|wait ?list|physician|practitioner|family doctor',re.I)

def extract(text):
    bs=BeautifulSoup(text,'html.parser')
    for bad in bs(['script','style','noscript','svg','header','footer','nav','form']):bad.decompose()
    # Collapse whitespace and use only meaningful content matching intake vocabulary.
    raw=' '.join(bs.stripped_strings)
    raw=re.sub(r'\s+',' ',raw)
    # Sentence boundaries are imperfect but deterministic; enough for an evidence-change alert.
    parts=re.split(r'(?<=[.!?])\s+|(?<=\n)\s*',raw)
    relevant=[p.strip()[:400] for p in parts if TERMS.search(p) and len(p.strip())>12]
    if not relevant: relevant=[raw[:1200]]
    return '\n'.join(relevant)[:9000]

def fetch_one(pair):
    url, meta=pair
    try:
        res=requests.get(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html'},timeout=(7,16),allow_redirects=True)
        res.raise_for_status()
        if 'html' not in res.headers.get('Content-Type','text/html').lower():raise ValueError('Response is not HTML')
        if len(res.content)>4_000_000:raise ValueError('Page too large')
        body=extract(res.text)
        if not body.strip():raise ValueError('No matching text')
        return url,{'hash':hashlib.sha256(body.encode()).hexdigest(),'error':None,'excerpt':body[:1400],'assessment':classify(body)}
    except Exception as exc:
        return url,{'hash':None,'error':str(exc)[:180]}

def run():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    pending_ids={(i['url'],i.get('new_hash')) for i in queue['items']}
    items=list(urlmap.items())
    changed=0;failed=0;baseline=0;ok=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for url,result in pool.map(fetch_one,items):
            prev=state['sources'].get(url,{})
            if result['error']:
                failed+=1
                state['sources'][url]={**prev,'last_attempt':now,'last_error':result['error']}
                continue
            ok+=1
            newhash=result['hash'];oldhash=prev.get('hash')
            state['sources'][url]={**prev,'hash':newhash,'excerpt':result['excerpt'][:1400],'possible_claim':result['assessment']['classification'],'last_attempt':now,'last_success':now,'last_error':None}
            if not oldhash:
                baseline+=1;continue
            if oldhash!=newhash and (url,newhash) not in pending_ids:
                changed+=1
                queue['items'].append({
                  'id':hashlib.sha256((url+newhash).encode()).hexdigest()[:12],
                  'detected_at':now,'url':url,'clinic_ids':urlmap[url]['clinics'],
                  'source_kind':urlmap[url]['kind'],'old_hash':oldhash,'new_hash':newhash,
                  'review_status':'pending',
                  'prior_excerpt':prev.get('excerpt','')[:900],
                  'current_excerpt':result['excerpt'][:1400],
                  'possible_claim':result['assessment']['classification'],
                  'matched_excerpts':result['assessment']['excerpts'],
                  'note':'A public source changed. Verify clinic-specific intake; do not infer opening or closure automatically.'})
    state['last_run']=now;state['last_summary']={'urls':len(items),'success':ok,'failed':failed,'new_baselines':baseline,'source_changes_queued':changed}
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    queue_path.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Source monitor:',state['last_summary'])
    if failed==len(items):
        print('WARNING: All source checks failed. Previous statuses are preserved; do not treat this as closures.',file=sys.stderr)
    return 0

if __name__=='__main__':sys.exit(run())
