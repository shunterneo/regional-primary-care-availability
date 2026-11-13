"""Public-source heartbeat; independent of deployment success and intake certainty."""
import datetime as dt, json
from collections import Counter
from urllib.parse import urlsplit
from common import ROOT

def assess(db, state, now):
    expected={c.get('evidence_url') for c in db['clinics'] if c.get('evidence_url') and c.get('operating_status') not in ('closed','archived')}
    sources=state.get('sources',{})
    missing=sorted(expected-set(sources))
    failed=[u for u in expected if sources.get(u,{}).get('last_error')]
    stale=[]
    for u in expected-set(missing):
        try:
            source_age=(now-dt.datetime.fromisoformat(sources[u]['last_success'].replace('Z','+00:00'))).total_seconds()/3600
        except (KeyError,TypeError,ValueError):source_age=None
        if source_age is None or source_age<0 or source_age>36:stale.append(u)
    try:
        age=(now-dt.datetime.fromisoformat(state['last_run'].replace('Z','+00:00'))).total_seconds()/3600
    except (KeyError,TypeError,ValueError):age=None
    problems=[]
    if age is None or age<0 or age>36:problems.append('Source monitor heartbeat missing or older than 36 hours')
    if missing:problems.append(f'{len(missing)} current evidence URLs have never been scanned')
    if stale:problems.append(f'{len(stale)} current evidence URLs lack a successful check in the last 36 hours')
    if failed:problems.append(f'{len(failed)} current evidence URLs failed their latest attempt')
    return {'checked_at':now.isoformat(),'last_source_scan':state.get('last_run'),
      'scan_age_hours':round(age,2) if age is not None else None,'expected_evidence_urls':len(expected),
      'failed_by_domain':dict(Counter(urlsplit(u).netloc for u in failed)),
      'failed_sources':[{'url':u,'category':sources[u].get('error_category','unclassified'),'error':sources[u].get('last_error')} for u in sorted(failed)],
      'unscanned_count':len(missing),'stale_source_count':len(stale),'failed_count':len(failed),'healthy':not problems,'problems':problems}

def current():
    return assess(json.loads((ROOT/'data/clinics.json').read_text()),json.loads((ROOT/'data/source_state.json').read_text()),dt.datetime.now(dt.timezone.utc))

if __name__=='__main__':
    result=current()
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['healthy'] else 1)
