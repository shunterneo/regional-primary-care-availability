"""Offline test: RSS discovery, dedup, evidence negation, no automatic publication."""
from __future__ import annotations
import json, tempfile, pathlib, sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import discover_clinics as d
from intake_evidence import classify
rss=b'''<rss><channel>
<item><title>New family medicine clinic opens in Woodstock</title><link>https://news.google.com/rss/articles/A1</link><pubDate>Wed, 11 Nov 2026 12:00:00 GMT</pubDate></item>
<item><title>Soccer team wins in London</title><link>https://news.google.com/rss/articles/A2</link></item>
<item><title>Brantford nurse practitioner clinic accepting new patients</title><link>https://news.google.com/rss/articles/A3</link></item>
</channel></rss>'''
assert len(d.parse_rss(rss))==3
assert d.relevant_headline('New family medicine clinic opens in Woodstock')
assert d.relevant_headline('Brantford nurse practitioner clinic accepting new patients')
assert not d.relevant_headline('New Andover Medical Centre opens - Islington Council News')
assert not d.relevant_headline('Waupaca Medical Centre opening new family practice - Wisconsin')
assert not d.relevant_headline('Chatham-Kent doctors accepting new patients')
assert not d.relevant_headline('New family clinic opens in London England')
assert not d.relevant_headline('London family clinic opens')  # London without Ontario is ambiguous
assert not d.relevant_headline('Ontario soccer team wins in Kitchener')
assert d.relevant_headline('Aylmer Ontario family physician retiring next month')
assert d.relevant_headline('Stratford nurse practitioner clinic opening a new office')
assert not d.relevant_headline('Toronto family doctor clinic accepting new patients')
assert not d.relevant_headline('Fort Erie new family medicine clinic accepting new patients')
assert classify('We are not accepting new patients at this time.')['classification']=='possible_closed'
assert classify('We are accepting new patients at this time.')['classification']=='possible_accepting'
assert classify('We are not accepting new patients. Another physician is accepting new patients.')['classification']=='conflicting_or_conditional'
assert classify('Our waitlist is currently open.')['classification']=='possible_waitlist'
with tempfile.TemporaryDirectory() as tmp:
    tmp=pathlib.Path(tmp)
    d.CONF=tmp/'config.json';d.QUEUE=tmp/'queue.json';d.STATE=tmp/'state.json'
    d.CONF.write_text(json.dumps({'queries_per_run':2,'queries':['woodstock family doctor','brantford doctor']}))
    d.QUEUE.write_text(json.dumps({'version':1,'items':[]}));d.STATE.write_text(json.dumps({'version':1,'seen':{},'last_run':None,'last_summary':{}}))
    before=(pathlib.Path(__file__).resolve().parents[1]/'data'/'clinics.json').read_bytes()
    with patch.object(d,'fetch_feed',return_value=d.parse_rss(rss)):
        d.run()
        q=json.loads(d.QUEUE.read_text())['items']
        assert len(q)==2 and all(x['within_75km']=='not verified' for x in q)
        d.run()
        assert len(json.loads(d.QUEUE.read_text())['items'])==2, 'Repeated leads should be deduplicated'
    after=(pathlib.Path(__file__).resolve().parents[1]/'data'/'clinics.json').read_bytes()
    assert before==after,'Discovery cannot auto-edit published clinics or statuses'
print('PASS: RSS parse, tentative discovery, evidence negation, duplicate protection, no automatic publication')
