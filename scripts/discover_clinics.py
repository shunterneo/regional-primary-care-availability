#!/usr/bin/env python3
"""Bounded, no-key RSS discovery of PUBLIC leads for new practices/intake notices.

Never enrolls patients, labels offices accepting, or alters the published clinic data.
Google News RSS is an unofficial discovery feed, not an exhaustive physician register.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, pathlib, re, sys
from urllib.parse import urlencode, urlparse
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from common import ROOT

DATA=ROOT/'data'; CONF=DATA/'search_queries.json'; QUEUE=DATA/'discovery_queue.json'; STATE=DATA/'discovery_state.json'
USER_AGENT='RegionalPrimaryCareDiscovery/2.0 (public news only; no patient data)'
HEALTH=re.compile(r'\b(?:family\s+(?:doctor|physician|medicine|practice)|primary\s+care|nurse\s+practitioner|medical\s+(?:clinic|centre|center)|health\s+centre|patient\s+attachment|new\s+patients?)\b',re.I)
ACTION=re.compile(r'\b(?:accept(?:ing)?|new|open(?:ing|ed)?|intake|enrol|register|attach|roster|wait\s?list|recruit|launch|expand|clos(?:e|ed|ing|ure)|retir(?:e|ed|ement)|relocat(?:e|ed|ion)|merg(?:e|ed|er)|new\s+(?:office|location|physician|doctor))\b',re.I)

def build_feed(query):
    return 'https://news.google.com/rss/search?'+urlencode({'q':query+' when:7d','hl':'en-CA','gl':'CA','ceid':'CA:en'})

def parse_rss(xml_bytes):
    # Strict size cap from fetcher prevents oversized XML or memory exhaustion.
    root=ET.fromstring(xml_bytes)
    out=[]
    for item in root.findall('.//channel/item')[:50]:
        val=lambda name: (item.findtext(name) or '').strip()
        title=BeautifulSoup(val('title'),'html.parser').get_text(' ',strip=True)[:240]
        url=val('link')[:1400]
        pub=val('pubDate')[:100]
        if not title or not url.startswith('https://'):continue
        if urlparse(url).netloc not in ('news.google.com','www.google.com'):continue
        out.append({'title':title,'url':url,'published':pub})
    return out

def fetch_feed(url):
    r=requests.get(url,headers={'User-Agent':USER_AGENT,'Accept':'application/rss+xml,application/xml'},timeout=(7,18),allow_redirects=True)
    r.raise_for_status()
    if len(r.content)>700_000:raise ValueError('RSS feed exceeds 700 KB cap')
    return parse_rss(r.content)

def run():
    conf=json.loads(CONF.read_text());state=json.loads(STATE.read_text());queue=json.loads(QUEUE.read_text())
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    queries=conf['queries'];take=min(conf.get('queries_per_run',12),len(queries))
    start=int(state.get('next_query_index',0))%len(queries)
    chosen=[queries[(start+i)%len(queries)] for i in range(take)]
    errors=[];found=0;queued=0;duplicates=0
    existing_ids={x['id'] for x in queue['items']}
    for query in chosen:
        try: items=fetch_feed(build_feed(query))
        except (requests.RequestException, ValueError, ET.ParseError) as exc:
            errors.append({'query':query,'error':str(exc)[:140]});continue
        for row in items:
            found+=1
            if not (HEALTH.search(row['title']) and ACTION.search(row['title'])):continue
            key=hashlib.sha256((row['url']+'|'+row['title']).encode()).hexdigest()[:16]
            if key in state['seen'] or key in existing_ids:
                duplicates+=1;continue
            state['seen'][key]=now
            queue['items'].append({
              'id':key,'detected_at':now,'title':row['title'],'news_link':row['url'],
              'published':row['published'],'matched_query':query,
              'source_type':'news_search_feed','proposed_action':'investigate clinic or intake',
              'within_75km':'not verified','current_intake':'not verified',
              'review_status':'pending',
              'note':'Lead only. Identify original source, exact office address, radius, current clinic-specific intake and eligibility.'})
            queued+=1
    # Limit history growth without forgetting recently detected duplicates.
    cutoff=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=180)).isoformat(timespec='seconds')
    state['seen']={k:v for k,v in state['seen'].items() if v>=cutoff}
    state['next_query_index']=(start+take)%len(queries)
    state['last_run']=now
    state['last_summary']={'queries_attempted':len(chosen),'queries_failed':len(errors),'feed_items_seen':found,'new_leads_queued':queued,'duplicates_skipped':duplicates,'errors':errors[:5]}
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n')
    QUEUE.write_text(json.dumps(queue,indent=2,ensure_ascii=False)+'\n')
    print('Discovery:',state['last_summary'])
    return 0
if __name__=='__main__':sys.exit(run())
