#!/usr/bin/env python3
"""Read curated public intake/clinic directories and surface unlisted candidates.

Directory statements are LEADS, never proof that a specific clinic is accepting
or closed. This job cannot edit published clinic records. No patient data.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from common import ROOT

DATA = ROOT / 'data'
CONF = DATA / 'curated_directories.json'
QUEUE = DATA / 'directory_queue.json'
STATE = DATA / 'directory_state.json'
CLINICS = DATA / 'clinics.json'
AGENT = 'RegionalPrimaryCareDiscovery/3.0 (public-directory research; no patient data)'
CARE = re.compile(r'\b(?:Dr\.?\s+[A-Z][A-Za-z]+|physician|family\s+(?:doctor|medicine|practice|health)|nurse\s+practitioner|(?:medical|primary\s+care|health)\s+(?:centre|center|clinic)|walk[- ]?in|health\s+team|NP[- ]?led)\b', re.I)
NEWS = re.compile(r'(?:family\s+(?:doctor|physician|medicine)|nurse\s+practitioner|primary\s+care|new\s+medical\s+clinic)', re.I)
ACTION = re.compile(r'(?:open(?:s|ed|ing)?|new\s+practice|accepting|registration|recruit|joined|joins|retir|clos(?:e|ed|ing|ure)|relocat|mov(?:e|ing)|expand)', re.I)
NOISE = re.compile(r'^(?:view|read more|information|contact|find a doctor|healthcare|health care connect|find services|health811|add to clipboard|doctors accepting new patients)$', re.I)


def norm(s):
    s = re.sub(r'\b(?:dr|doctor|doctors|medical|centre|center|clinic|family|health|practice|physician|unit|site|location|inc)\b', ' ', s or '', flags=re.I)
    return re.sub(r'[^a-z0-9]', '', s.lower())


def canonical(s):
    return re.sub(r'\s+', ' ', BeautifulSoup(str(s or ''), 'html.parser').get_text(' ', strip=True)).strip()


def fingerprint(items):
    return hashlib.sha256('\n'.join(sorted(x['key']+'|'+x['excerpt'] for x in items)).encode()).hexdigest()


def candidate(title, detail, link, source, scope):
    title=canonical(title)[:180]
    detail=canonical(detail)[:440]
    if len(title)<5 or NOISE.fullmatch(title):return None
    key=norm(title)
    if len(key)<4:return None
    return {'key': key, 'title':title,'excerpt':detail, 'link': link or source['url'], 'scope': scope}


def parse_candidates(html, source):
    """Conservative deterministic extraction; no AI inference from directory text."""
    soup=BeautifulSoup(html,'html.parser')
    for t in soup(['script','style','noscript','svg','footer','nav','form']):t.decompose()
    mode=source['mode'];out=[]
    if mode=='news':
        for a in soup.select('a[href]'):
            title=canonical(a.get_text(' ',strip=True))
            link=urljoin(source['url'], a['href'])
            if not (NEWS.search(title) and ACTION.search(title)):continue
            # Avoid internal arbitrary endpoints, and external links or javascript.
            if urlparse(link).netloc.lower()!=urlparse(source['url']).netloc.lower():continue
            row=candidate(title,title,link,source,'announcement only; no current intake proven')
            if row:out.append(row)
    elif mode=='table':
        for tr in soup.select('tr'):
            cells=[canonical(td.get_text(' ',strip=True)) for td in tr.find_all(['td','th'],recursive=False)]
            if not cells or not CARE.search(' '.join(cells)):continue
            if len(cells)>1 and cells[1].strip().lower()=='address':continue
            name=cells[0];detail=' · '.join(cells[:5])
            if not CARE.search(name) and len(cells)>1:name=cells[1]
            a=tr.find('a',href=True)
            link=urljoin(source['url'],a['href']) if a else source['url']
            if urlparse(link).scheme!='https':link=source['url']
            row=candidate(name,detail,link,source,'directory entry; verify original clinic intake')
            if row:out.append(row)
    elif mode=='people':
        # London association usually places named practices in an ordered list.
        for li in soup.select('ol li'):
            value=canonical(li.get_text(' ',strip=True))
            if not CARE.search(value):continue
            heading=li.find(['h3','h4','strong','b'])
            title=canonical(heading.get_text(' ',strip=True)) if heading else re.split(r'(?:\.|\s{2,})',value,maxsplit=1)[0]
            if len(title)<8:title=value[:100]
            row=candidate(title,value,source['url'],source,'provider directory; status must be rechecked')
            if row:out.append(row)
        # Some web layouts use paragraphs or headers instead of LI elements.
        for h in soup.select('h2,h3,h4,strong,b'):
            text=canonical(h.get_text(' ',strip=True))
            if len(text)>180 or not CARE.search(text):continue
            row=candidate(text,text,source['url'],source,'provider directory; status must be rechecked')
            if row:out.append(row)
        if not out:
            # Brant hospital and similar directories sometimes use unstructured
            # paragraphs instead of HTML list elements.
            for line in soup.get_text('\n',strip=True).splitlines():
                value=canonical(line)
                if not (8<=len(value)<=160 and CARE.search(value)):continue
                if re.search(r'\b(?:health ?care connect|health811|family doctors accepting|physician register)\b',value,re.I):continue
                row=candidate(value,value,source['url'],source,'regional provider directory; current intake unverified')
                if row:out.append(row)
    elif mode=='cards':
        for item in soup.select('article, .listing, .service, .card, tr'):
            body=canonical(item.get_text(' ',strip=True))
            if not CARE.search(body) or len(body)>900:continue
            heading=item.find(['h2','h3','h4','strong','td'])
            title=canonical(heading.get_text(' ',strip=True)) if heading else body[:110]
            row=candidate(title,body,source['url'],source,'facility directory; does not establish intake')
            if row:out.append(row)
    elif mode=='page':
        # OHT resource page: flag only when meaningful public text changes.
        body=canonical(soup.get_text(' ',strip=True))
        if body:
            return [{'key':'page','title':source['name'],'excerpt':body[:440], 'link':source['url'],'scope':'resource notice; no clinic-specific intake claim'}]
    # Directory HTML may change markup. If candidate count=0, do not erase old results.
    uniq={}
    for item in out:
        if item['key'] not in uniq:uniq[item['key']]=item
    return list(uniq.values())[:120]


def fetch_html(source):
    url=source['url']
    if not url.startswith('https://'):raise ValueError('HTTPS required')
    r=requests.get(url,headers={'User-Agent':AGENT,'Accept':'text/html'},timeout=(7,18),allow_redirects=True)
    r.raise_for_status()
    if urlparse(r.url).hostname!=urlparse(url).hostname:raise ValueError('Redirect changed directory host')
    if 'html' not in r.headers.get('Content-Type','text/html').lower():raise ValueError('Not HTML')
    if len(r.content)>1_500_000:raise ValueError('Oversized directory page')
    return r.text


def known_match(row,clinics):
    name=norm(row['title']);
    if len(name)<7:return []
    hits=[]
    for clinic in clinics:
        fields=[clinic.get('name',''), clinic.get('providers','')]
        for field in fields:
            n=norm(field)
            if n and ((name in n or n in name) and min(len(name),len(n))>=7):
                hits.append(clinic['id']);break
    return hits[:5]


def process(sources,html_map,state,queue,clinics,day):
    summary={'sources':len(sources),'success':0,'failed':0,'baselines':0,'new_directory_leads':0,'listing_removals_to_review':0,'errors':[]}
    existing_ids={p['id'] for p in queue['items']}
    for source in sources:
        sid=source['id'];prev=state['sources'].get(sid,{})
        html=html_map.get(sid)
        if html is None:
            summary['failed']+=1
            state['sources'][sid]={**prev,'last_attempt':day,'last_error':'unavailable; preserved previous results'}
            continue
        rows=parse_candidates(html,source)
        if not rows:
            summary['failed']+=1
            state['sources'][sid]={**prev,'last_attempt':day,'last_error':'no extractable entries; preserved previous results'}
            continue
        summary['success']+=1
        old=prev.get('entries',{})
        current={x['key']:x for x in rows}
        if not prev.get('last_success'):summary['baselines']+=1
        for key,row in current.items():
            if key in old:
                if old[key].get('excerpt') != row['excerpt']:
                    digest=hashlib.sha256(row['excerpt'].encode()).hexdigest()[:12]
                    ident=hashlib.sha256((sid+'|changed|'+key+'|'+digest).encode()).hexdigest()[:18]
                    if ident not in existing_ids:
                        queue['items'].append({'id':ident,'detected_at':day,'title':row['title'],
                          'url':row['link'],'source_directory':sid,'source_name':source['name'],
                          'review_status':'pending','proposed_action':'Check modified directory text; confirm clinic-specific ongoing patient intake if applicable',
                          'prior_excerpt':old[key].get('excerpt','')[:440],'current_excerpt':row['excerpt'],
                          'intake_status':'unconfirmed','radius_checked':False,
                          'note':'Content change is NOT evidence of intake opening, closure or permanent practice closure.'})
                        existing_ids.add(ident)
                        summary['new_directory_leads']+=1
                continue
            if source['mode']=='page':continue  # First visit is a monitoring baseline, not a new practice.
            hits=known_match(row,clinics)
            if hits:continue # Already-listed clinic; directory change is not a new clinic.
            ident=hashlib.sha256((sid+'|'+key).encode()).hexdigest()[:18]
            if ident in existing_ids:continue
            queue['items'].append({'id':ident,'detected_at':day,'title':row['title'],
                'url':row['link'],'source_directory':sid,'source_name':source['name'],
                'excerpt':row['excerpt'],'source_scope':row['scope'],'review_status':'pending',
                'proposed_action':'Verify practice identity, street address, provider, care model, 75km boundary, and direct official intake',
                'intake_status':'unconfirmed','radius_checked':False,
                'note':'A third-party directory or news title is a research lead, not current acceptance evidence.'})
            existing_ids.add(ident);summary['new_directory_leads']+=1
        # Only after successful extraction can a disappearing entry be flagged.
        for key,row in old.items():
            if key in current:continue
            ident=hashlib.sha256((sid+'|removed|'+key).encode()).hexdigest()[:18]
            if ident in existing_ids:continue
            queue['items'].append({'id':ident,'detected_at':day,'title':row['title'],
                'url':source['url'],'source_directory':sid,'source_name':source['name'],
                'review_status':'pending','proposed_action':'Check whether directory listing was removed or renamed',
                'intake_status':'unconfirmed','radius_checked':False,
                'note':'Removal from one webpage is NEVER proof that intake closed or that the clinic closed.'})
            existing_ids.add(ident);summary['listing_removals_to_review']+=1
        state['sources'][sid]={'entries':current,'last_attempt':day,'last_success':day,'last_error':None,
                               'entry_count':len(rows),'fingerprint':fingerprint(rows)}
    state['last_run']=day;state['last_summary']=summary
    return summary


def run():
    sources=json.loads(CONF.read_text())
    state=json.loads(STATE.read_text());queue=json.loads(QUEUE.read_text());clinics=json.loads(CLINICS.read_text())['clinics']
    day=dt.date.today().isoformat()
    pages={};errors=[]
    for src in sources:
        try:pages[src['id']]=fetch_html(src)
        except (requests.RequestException,ValueError) as exc:
            pages[src['id']]=None;errors.append({'source':src['id'],'error':str(exc)[:130]})
    summary=process(sources,pages,state,queue,clinics,day)
    summary['errors']=errors[:12]
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    QUEUE.write_text(json.dumps(queue,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('Regional directory discovery:',summary)
    return 0

if __name__=='__main__':raise SystemExit(run())
