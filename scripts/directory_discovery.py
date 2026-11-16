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
EXTRACTION_VERSION = 'directory-v3'
MAX_ENTRIES = 120
MAX_HTML_BYTES = 1_500_000
MAX_PAGE_LINKS = 500
HEALTHLINE_ROOTS = ('southwesthealthline.ca','healthline.ca')
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
    return hashlib.sha256('\n'.join(sorted(x['key']+'|'+x['content_hash'] for x in items)).encode()).hexdigest()


def candidate(title, detail, link, source, scope):
    full_title=canonical(title)
    full_detail=canonical(detail)
    title=full_title[:180]
    detail=full_detail[:440]
    if len(title)<5 or NOISE.fullmatch(title):return None
    key=norm(title)
    if len(key)<4:return None
    return {'key': key, 'title':title,'excerpt':detail, 'link': link or source['url'], 'scope': scope,
            'content_hash': hashlib.sha256(json.dumps([full_title, full_detail, link or source['url']], ensure_ascii=False).encode()).hexdigest()}


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
            name=cells[0];detail=' · '.join(cells)
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
            if not CARE.search(body):continue
            heading=item.find(['h2','h3','h4','strong','td'])
            title=canonical(heading.get_text(' ',strip=True)) if heading else body[:110]
            row=candidate(title,body,source['url'],source,'facility directory; does not establish intake')
            if row:out.append(row)
    elif mode=='healthline':
        # Healthline listServices pages link individual service entries directly.
        # Each is a discovery lead only; their patient-intake status is not verified.
        for a in soup.select('a[href]'):
            href=urljoin(source['url'],a.get('href',''))
            parsed=urlparse(href)
            if parsed.scheme!='https' or not parsed.hostname:continue
            if not any(parsed.hostname==root or parsed.hostname.endswith('.'+root) for root in HEALTHLINE_ROOTS):continue
            if 'displayservice.aspx' not in parsed.path.lower():continue
            title=canonical(a.get_text(' ',strip=True))
            if len(title)<7 or NOISE.fullmatch(title):continue
            parent=a.find_parent(['tr','li','p','div'])
            detail=canonical(parent.get_text(' ',strip=True)) if parent else title
            row=candidate(title,detail,href,source,'regional practice listing; verify address, care model and intake directly')
            if row:out.append(row)
    elif mode=='page':
        # OHT resource page: flag only when meaningful public text changes.
        body=canonical(soup.get_text(' ',strip=True))
        if body:
            links=public_page_links(soup,source['url'])
            return [{'key':'page','title':source['name'],'excerpt':body[:440], 'link':source['url'],
                     'content_hash':hashlib.sha256(json.dumps({'text':body,'links':links},sort_keys=True).encode()).hexdigest(),
                     'scope':'resource notice; no clinic-specific intake claim'}]
    # Directory HTML may change markup. If candidate count=0, do not erase old results.
    uniq={}
    for item in out:
        if item['key'] not in uniq:uniq[item['key']]=item
    if len(uniq)>MAX_ENTRIES:
        raise ExtractionError('extraction_limit', 'Entry limit exceeded; partial extraction is not a complete directory')
    return list(uniq.values())


def fetch_html(source):
    url=source['url']
    if not url.startswith('https://'):raise ValueError('HTTPS required')
    r=requests.get(url,headers={'User-Agent':AGENT,'Accept':'text/html'},timeout=(7,18),allow_redirects=True)
    r.raise_for_status()
    if urlparse(r.url).scheme!='https' or urlparse(r.url).hostname!=urlparse(url).hostname:raise ValueError('Redirect changed directory HTTPS origin')
    if 'html' not in r.headers.get('Content-Type','text/html').lower():raise ValueError('Not HTML')
    if len(r.content)>MAX_HTML_BYTES:raise ValueError('Oversized directory page')
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


class ExtractionError(ValueError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category=category


def public_page_links(soup,source_url):
    """Hash bounded public navigation targets, without fetching links or assets."""
    base=source_url
    base_node=soup.find('base',href=True)
    if base_node:
        proposed=urljoin(source_url,base_node['href'])
        parsed=urlparse(proposed)
        if parsed.scheme in ('http','https') and parsed.hostname and not parsed.username and not parsed.password:
            base=proposed
    nodes=soup.select('a[href],area[href]')
    if len(nodes)>MAX_PAGE_LINKS:
        raise ExtractionError('extraction_limit','Public page link limit exceeded; no truncated baseline')
    links=set()
    for node in nodes:
        target=urljoin(base,node['href'])
        parsed=urlparse(target)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:continue
        if len(target)>4096:raise ExtractionError('extraction_limit','Public link exceeds bounded URL length')
        links.add(target)
    return sorted(links)


def fetch_error_category(exc):
    if isinstance(exc,requests.exceptions.SSLError):return 'tls_error'
    if isinstance(exc,(requests.Timeout,requests.ConnectionError)):return 'transient_network'
    if isinstance(exc,requests.HTTPError):
        status=getattr(exc.response,'status_code',None)
        if status in (401,403):return 'blocked_access'
        if status==429 or (status is not None and status>=500):return 'transient_http'
        return 'http_error'
    return 'fetch_invalid_content'


def source_signature(source):
    return hashlib.sha256(json.dumps({key:source.get(key) for key in ('url','mode')},sort_keys=True).encode()).hexdigest()


def successful_state(current,rows,day,signature,reason,event_sequence):
    return {'entries':current,'last_attempt':day,'last_success':day,'last_error':None,
            'error_category':None,'entry_count':len(rows),'fingerprint':fingerprint(rows),
            'extraction_version':EXTRACTION_VERSION,'source_signature':signature,
            'baseline_reason':reason,'event_sequence':event_sequence}


def extract_snapshot(html,source):
    """A readable, complete extraction or a typed failure; no silent partial state.

    Empty *relevant* news is normal. Empty provider extraction is ambiguous and
    preserves the prior baseline. These are discovery leads, not intake proof.
    """
    if not isinstance(html,str):raise ExtractionError('invalid_content','Expected HTML text')
    if len(html.encode())>MAX_HTML_BYTES:raise ExtractionError('oversized_content','Directory exceeds bounded HTML size')
    if source.get('mode') not in ('news','table','people','cards','healthline','page'):
        raise ExtractionError('extraction_schema','Unsupported directory mode')
    soup=BeautifulSoup(html,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    noscript=' '.join(x.get_text(' ',strip=True) for x in soup.find_all('noscript'))
    has_script=bool(soup.find('script'))
    for node in soup(['script','style','noscript','template','svg','head','nav','footer','form']):node.decompose()
    plain=canonical(soup.get_text(' ',strip=True))
    challenge=r'just a moment[.!…]*|access denied|attention required!?|verify (?:you are|that you are) human|checking your browser'
    if re.fullmatch(challenge,title.strip(),re.I) or re.match(challenge,plain,re.I):
        raise ExtractionError('blocked_page','Access challenge or denial; no bypass attempted')
    if re.search(r'\b(?:sign|log) in to (?:continue|view|access)\b',title+' '+plain,re.I):
        raise ExtractionError('login_required','Authentication required; no login attempted')
    if re.fullmatch(r'(?:404(?:\s*[-:|]\s*.*)?|page not found|service unavailable|internal server error)',title.strip(),re.I):
        raise ExtractionError('error_page','Error document returned instead of directory')
    js=r'(?:enable|requires?|need).*javascript|javascript.*(?:required|enabled)'
    if (len(plain)<500 and re.search(js,plain+' '+noscript,re.I)) or (len(plain)<12 and has_script):
        raise ExtractionError('render_required','JavaScript shell; no readable directory extraction')
    if len(plain)<12:raise ExtractionError('empty_content','No meaningful directory text')
    rows=parse_candidates(html,source)
    if not rows:
        if source['mode']=='news':
            # Require a recognizable news index/explicit empty feed, not any
            # arbitrary HTTP200 document that happens to contain no matches.
            heading=' '.join(x.get_text(' ',strip=True) for x in soup.find_all(['h1','h2']))
            same_host_links=[a for a in soup.select('a[href]')
                             if urlparse(urljoin(source['url'],a['href'])).hostname==urlparse(source['url']).hostname
                             and canonical(a.get_text(' ',strip=True))]
            empty_feed=re.search(r'\bno (?:news|articles|posts|results)(?:\s+(?:found|available|at this time))?\b',plain,re.I)
            if (re.search(r'\b(?:news|announcements|media releases)\b',title+' '+heading,re.I) and same_host_links) or empty_feed:
                return []
        raise ExtractionError('extraction_schema','No extractable entries; source layout or contents require review')
    required={'key','title','excerpt','link','scope','content_hash'}
    if any(not required.issubset(row) or not re.fullmatch(r'[0-9a-f]{64}',row.get('content_hash','')) for row in rows):
        raise ExtractionError('extraction_schema','Invalid extracted entry schema')
    if len({row['key'] for row in rows})!=len(rows):
        raise ExtractionError('extraction_schema','Duplicate extracted entry keys')
    return rows


def process(sources,html_map,state,queue,clinics,day,fetch_errors=None):
    summary={'sources':len(sources),'success':0,'failed':0,'baselines':0,'version_baselines':0,'zero_result_news':0,'new_directory_leads':0,'listing_removals_to_review':0,'errors':[]}
    existing_ids={p['id'] for p in queue['items']}
    for source in sources:
        sid=source['id'];prev=state['sources'].get(sid,{})
        html=html_map.get(sid)
        error=(fetch_errors or {}).get(sid)
        try:
            if html is None:
                raise ExtractionError((error or {}).get('category','fetch_unavailable'), (error or {}).get('error','Source unavailable'))
            rows=extract_snapshot(html,source)
        except (ExtractionError,ValueError,TypeError,KeyError) as exc:
            summary['failed']+=1
            category=getattr(exc,'category','extraction_schema')
            message=str(exc)[:800]
            state['sources'][sid]={**prev,'last_attempt':day,'last_error':message+'; preserved previous results','error_category':category}
            summary['errors'].append({'source':sid,'category':category,'error':message})
            continue
        summary['success']+=1
        if source['mode']=='news' and not rows:summary['zero_result_news']+=1
        old=prev.get('entries',{})
        current={x['key']:x for x in rows}
        signature=source_signature(source)
        first_baseline=not prev.get('last_success')
        migration=not first_baseline and (prev.get('extraction_version')!=EXTRACTION_VERSION or prev.get('source_signature')!=signature)
        # Sequence identifies observed transitions, not the resulting content.
        # Returning to a previously seen value can therefore alert again; an
        # unchanged retry never increments the sequence or repeats an event.
        prior_sequence=prev.get('event_sequence',0)
        if type(prior_sequence) is not int or prior_sequence<0:prior_sequence=0
        changed=not first_baseline and not migration and prev.get('fingerprint')!=fingerprint(rows)
        event_sequence=prior_sequence+int(changed)
        if first_baseline or migration:summary['baselines']+=1
        if migration:summary['version_baselines']+=1
        # A new parser/configuration establishes its own baseline. It cannot
        # interpret extraction differences as actual directory changes/removals.
        if migration:
            state['sources'][sid]=successful_state(current,rows,day,signature,'extraction_version_or_source_changed',prior_sequence)
            continue
        for key,row in current.items():
            if key in old:
                if old[key].get('content_hash') != row['content_hash']:
                    digest=row['content_hash'][:12]
                    ident=hashlib.sha256((sid+'|changed|'+str(event_sequence)+'|'+key+'|'+digest).encode()).hexdigest()[:18]
                    if ident not in existing_ids:
                        queue['items'].append({'id':ident,'detected_at':day,'title':row['title'],
                          'url':row['link'],'source_directory':sid,'source_name':source['name'],
                          'extraction_version':EXTRACTION_VERSION,'source_signature':signature,'source_url':source['url'],'source_mode':source['mode'],'event_sequence':event_sequence,
                          'review_status':'pending','proposed_action':'Check modified directory text; confirm clinic-specific ongoing patient intake if applicable',
                          'prior_excerpt':old[key].get('excerpt','')[:440],'current_excerpt':row['excerpt'],
                          'prior_content_hash':old[key].get('content_hash'),'current_content_hash':row['content_hash'],
                          'preview_unchanged':old[key].get('excerpt')==row['excerpt'],
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
                'extraction_version':EXTRACTION_VERSION,'source_signature':signature,'source_url':source['url'],'source_mode':source['mode'],'event_sequence':event_sequence,
                'excerpt':row['excerpt'],'source_scope':row['scope'],'review_status':'pending',
                'proposed_action':'Verify practice identity, street address, provider, care model, 75km boundary, and direct official intake',
                'intake_status':'unconfirmed','radius_checked':False,
                'note':'A third-party directory or news title is a research lead, not current acceptance evidence.'})
            existing_ids.add(ident);summary['new_directory_leads']+=1
        # Only after successful extraction can a disappearing entry be flagged.
        for key,row in old.items():
            # News windows rotate; article expiry is not a listing removal.
            if source['mode']=='news' or key in current:continue
            ident=hashlib.sha256((sid+'|removed|'+str(event_sequence)+'|'+key).encode()).hexdigest()[:18]
            if ident in existing_ids:continue
            queue['items'].append({'id':ident,'detected_at':day,'title':row['title'],
                'url':source['url'],'source_directory':sid,'source_name':source['name'],
                'extraction_version':EXTRACTION_VERSION,'source_signature':signature,'source_url':source['url'],'source_mode':source['mode'],'event_sequence':event_sequence,
                'review_status':'pending','proposed_action':'Check whether directory listing was removed or renamed',
                'intake_status':'unconfirmed','radius_checked':False,
                'note':'Removal from one webpage is NEVER proof that intake closed or that the clinic closed.'})
            existing_ids.add(ident);summary['listing_removals_to_review']+=1
        state['sources'][sid]=successful_state(current,rows,day,signature,'first_observation' if first_baseline else None,event_sequence)
    state['last_run']=day;state['last_summary']=summary
    return summary


def run():
    sources=json.loads(CONF.read_text())
    state=json.loads(STATE.read_text());queue=json.loads(QUEUE.read_text());clinics=json.loads(CLINICS.read_text())['clinics']
    day=dt.date.today().isoformat()
    pages={};errors={}
    for src in sources:
        try:pages[src['id']]=fetch_html(src)
        except (requests.RequestException,ValueError) as exc:
            pages[src['id']]=None;errors[src['id']]={'category':fetch_error_category(exc),'error':str(exc)[:800]}
    summary=process(sources,pages,state,queue,clinics,day,fetch_errors=errors)
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    QUEUE.write_text(json.dumps(queue,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('Regional directory discovery:',summary)
    return 0

if __name__=='__main__':raise SystemExit(run())
