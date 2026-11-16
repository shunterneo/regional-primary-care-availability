"""Read-only stage health, distinct from deployment success or intake certainty.

assess(db,state,now) retains the original evidence-only API. current() uses
assess_all() for all configured automated monitoring stages. Date-only clocks
expose uncertainty rather than inventing a time or declaring a doubtful green.
"""
import datetime as dt
import json
import hashlib
import re
from collections import Counter
from urllib.parse import urlsplit
from common import ROOT

MAX_AGE_HOURS=36
UTC=dt.timezone.utc


def clock(value,now):
    """Freshness interval for a timestamp or recorded calendar day (UTC)."""
    now=now.astimezone(UTC)
    shown=value[:200] if isinstance(value,str) else (None if value is None else repr(value)[:200])
    result={'value':shown,'precision':None,'status':'missing','age_hours_min':None,'age_hours_max':None}
    if value is None:return result
    if not isinstance(value,str):return {**result,'status':'invalid'}
    try:
        if len(value)==10:
            day=dt.date.fromisoformat(value)
            if day>now.date():return {**result,'precision':'date','status':'future'}
            start=dt.datetime.combine(day,dt.time.min,UTC)
            end=min(start+dt.timedelta(days=1),now)
            low=(now-end).total_seconds()/3600
            high=(now-start).total_seconds()/3600
            precision='date'
        else:
            stamp=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
            if stamp.tzinfo is None:return {**result,'precision':'timestamp','status':'invalid'}
            stamp=stamp.astimezone(UTC)
            if stamp>now:return {**result,'precision':'timestamp','status':'future'}
            low=high=(now-stamp).total_seconds()/3600
            precision='timestamp'
        status='fresh' if high<=MAX_AGE_HOURS else ('stale' if low>MAX_AGE_HOURS else 'freshness_uncertain')
        return {**result,'precision':precision,'status':status,'age_hours_min':round(low,2),'age_hours_max':round(high,2)}
    except (TypeError,ValueError):return {**result,'status':'invalid'}


def _count(value):return type(value) is int and value>=0

def _impossible_success_order(success,attempt):
    # Only reject a provable contradiction; date-only intervals can overlap.
    return success.get('age_hours_max') is not None and attempt.get('age_hours_min') is not None and success['age_hours_max']<attempt['age_hours_min']

def _https(value):
    try:
        parsed=urlsplit(value)
        return isinstance(value,str) and len(value)<=4096 and parsed.scheme=='https' and bool(parsed.hostname) and not parsed.username and not parsed.password
    except (TypeError,ValueError,AttributeError):return False


def _summary(stage):
    """Required-stage result, retaining partial success rather than a false green."""
    stage['healthy']=not stage['problems']
    if stage['healthy']:stage['status']='healthy'
    elif stage.get('invalid_count',0) or stage.get('schema_errors'):stage['status']='invalid' if not stage.get('successful_count') else 'degraded'
    elif stage.get('successful_count'):stage['status']='degraded'
    elif stage.get('failed_count'):stage['status']='failed'
    elif stage.get('stale_count'):stage['status']='stale'
    else:stage['status']='unavailable'
    return stage


def _base():
    return {'required':True,'healthy':False,'status':'unavailable','expected_count':0,'successful_count':0,
            'failed_count':0,'stale_count':0,'unscanned_count':0,'invalid_count':0,'uncertain_count':0,
            'problems':[],'schema_errors':[]}


def _urls(config):
    if not isinstance(config,list) or not config:raise ValueError('Expected a nonempty configured source list')
    out=[]
    for item in config:
        if not isinstance(item,dict) or not isinstance(item.get('url'),str) or not _https(item['url']):
            raise ValueError('Invalid configured HTTPS source URL')
        out.append(item['url'])
    return sorted(set(out))


def _evidence_urls(db):
    if not isinstance(db,dict) or not isinstance(db.get('clinics'),list) or not db['clinics']:
        raise ValueError('Clinic inventory unavailable or invalid')
    if any(not isinstance(c,dict) for c in db['clinics']):raise ValueError('Invalid clinic record')
    for c in db['clinics']:
        if c.get('evidence_url') and (not _https(c['evidence_url'])):raise ValueError('Invalid clinic evidence URL')
    return sorted({c['evidence_url'] for c in db['clinics'] if c.get('evidence_url') and c.get('operating_status') not in ('closed','archived')})


def _coverage(expected,state,now,directories=False,config_errors=None):
    stage=_base();stage['expected_count']=len(expected);stage['items']=[]
    stage['schema_errors'].extend(config_errors or [])
    if not isinstance(state,dict):
        stage['schema_errors'].append('Monitoring state missing or invalid')
        state={}
    sources=state.get('sources')
    if not isinstance(sources,dict):
        stage['schema_errors'].append('Source-state map missing or invalid');sources={}
    run=clock(state.get('last_run'),now);stage['last_run']=run
    if run['status']!='fresh':stage['problems'].append('Stage clock '+run['status'])
    for ident,meta in expected.items():
        rec=sources.get(ident)
        item={'id':ident,**meta,'error':None,'category':None,'freshness':clock(None,now),'status':'unscanned'}
        if rec is None:
            stage['unscanned_count']+=1
        elif not isinstance(rec,dict):
            item['status']='invalid';stage['invalid_count']+=1
        else:
            fresh=clock(rec.get('last_success'),now);item['freshness']=fresh
            attempted=clock(rec.get('last_attempt'),now);item['last_attempt']=attempted
            error=rec.get('last_error');item['error']=error[:600] if isinstance(error,str) else (None if error is None else repr(error)[:200]);item['category']=rec.get('error_category') or 'unclassified'
            invalid=error is not None and not isinstance(error,str)
            invalid=invalid or fresh['status'] in ('invalid','future') or attempted['status'] in ('invalid','future') or _impossible_success_order(fresh,attempted)
            if directories and fresh['status']=='fresh' and not error:
                entries=rec.get('entries');n=rec.get('entry_count')
                invalid=invalid or not isinstance(entries,dict) or not _count(n) or (isinstance(entries,dict) and n!=len(entries)) or (n==0 and meta.get('mode')!='news')
            if invalid:item['status']='invalid';stage['invalid_count']+=1
            elif error:item['status']='failed';stage['failed_count']+=1
            elif fresh['status']=='fresh':item['status']='healthy';stage['successful_count']+=1
            elif fresh['status']=='freshness_uncertain':item['status']='freshness_uncertain';stage['uncertain_count']+=1
            else:item['status']='stale';stage['stale_count']+=1
            # Age is a separate fact from failure: both can apply to one source.
            item['stale']=fresh['status'] in ('stale','missing')
        stage['items'].append(item)
    for field,label in [('failed_count','latest checks failed'),('stale_count','sources lack a fresh successful check'),('unscanned_count','configured sources unscanned'),('invalid_count','source records malformed or future-dated'),('uncertain_count','date-only source clocks cannot establish 36-hour freshness')]:
        if stage[field]:stage['problems'].append(f'{stage[field]} {label}')
    stage['stale_success_count']=sum(bool(x.get('stale')) for x in stage['items'])
    stage['items_scope']='attention_only'
    stage['healthy_items_omitted']=stage['successful_count']
    stage['items']=[item for item in stage['items'] if item['status']!='healthy']
    stage['problems'].extend(stage['schema_errors'])
    return _summary(stage)


def assess(db,state,now):
    """Backward-compatible evidence-only view; not whole-system health."""
    try:urls=_evidence_urls(db);errors=[]
    except (ValueError,TypeError,KeyError) as exc:urls=[];errors=[str(exc)]
    stage=_coverage({u:{'url':u} for u in urls},state,now,config_errors=errors)
    failed=[x for x in stage['items'] if x['error']]
    stale=[x for x in stage['items'] if x.get('stale') or x['status'] in ('stale','invalid','freshness_uncertain')]
    age=stage['last_run']['age_hours_max']
    return {'checked_at':now.isoformat(),'last_source_scan':state.get('last_run') if isinstance(state,dict) else None,
            'scan_age_hours':age,'expected_evidence_urls':len(urls),
            'failed_by_domain':dict(Counter(urlsplit(x['url']).netloc for x in failed)),
            'failed_sources':[{'url':x['url'],'category':x['category'],'error':x['error']} for x in failed],
            'unscanned_count':stage['unscanned_count'],'stale_source_count':len(stale),
            'failed_count':len(failed),'healthy':stage['healthy'],'problems':stage['problems']}


def _batch_summary_valid(summary,keys):
    return isinstance(summary,dict) and all(_count(summary.get(k)) for k in keys)


def _news(conf,state,now):
    stage=_base();stage['coverage_scope']='latest_rotating_query_batch'
    stage['limitation']='No per-query last-success history; latest batch is not proof all configured queries were recently checked.'
    try:
        queries=conf['queries'];take=conf['queries_per_run']
        if not isinstance(queries,list) or not queries or any(not isinstance(q,str) or not q.strip() for q in queries) or len(set(queries))!=len(queries) or not _count(take) or take==0:raise ValueError()
        stage['configured_queries']=len(queries);stage['expected_count']=min(take,len(queries))
    except (TypeError,KeyError,ValueError):stage['schema_errors'].append('News query configuration missing or invalid')
    if not isinstance(state,dict):state={};stage['schema_errors'].append('News discovery state missing or invalid')
    stage['last_run']=clock(state.get('last_run'),now)
    if stage['last_run']['status']!='fresh':stage['problems'].append('News stage clock '+stage['last_run']['status'])
    summary=state.get('last_summary')
    if not _batch_summary_valid(summary,('queries_attempted','queries_failed')):
        stage['schema_errors'].append('News batch counts missing or invalid')
    else:
        attempted=summary['queries_attempted'];failed=summary['queries_failed']
        stage['attempted_count']=attempted;stage['failed_count']=failed
        if failed>attempted or attempted>stage['expected_count']:stage['schema_errors'].append('News batch counts inconsistent with configuration')
        else:
            stage['last_batch_successful_count']=attempted-failed
            stage['successful_count']=attempted-failed if stage['last_run']['status']=='fresh' else 0
            stage['unscanned_count']=stage['expected_count']-attempted
            if stage['last_run']['status']=='stale':stage['stale_count']=attempted-failed
            if stage['last_run']['status']=='freshness_uncertain':stage['uncertain_count']=attempted-failed
            if failed:stage['problems'].append(f'{failed} news queries failed')
            if stage['unscanned_count']:stage['problems'].append(f"{stage['unscanned_count']} scheduled query slots unattempted")
        errors=summary.get('errors')
        if not isinstance(errors,list) or len(errors)>failed or any(not isinstance(e,dict) or not isinstance(e.get('error'),str) for e in errors):stage['schema_errors'].append('News error details malformed')
        else:
            stage['errors']=[{'query':str(e.get('query',''))[:240],'error':e['error'][:600]} for e in errors[:20]]
            stage['error_details_omitted']=max(0,len(errors)-20)
            stage['error_details_complete']=len(stage['errors'])>=failed
    stage['problems'].extend(stage['schema_errors']);return _summary(stage)


def _registry(state,now):
    stage=_base();stage['expected_count']=1
    if not isinstance(state,dict):state={};stage['schema_errors'].append('Official registry state missing or invalid')
    stage['last_run']=clock(state.get('last_run'),now)
    if 'last_success' in state:
        value=state.get('last_success');stage['success_clock_basis']='explicit_last_success'
    else:
        value=state.get('last_run');stage['success_clock_basis']='legacy_completed_run'
        stage['limitation']='Legacy schema records completion date only; it has no explicit transport-success timestamp.'
    stage['last_success']=clock(value,now);stage['last_attempt']=clock(state.get('last_attempt'),now)
    for name in ('last_run','last_success'):
        if stage[name]['status']!='fresh':stage['problems'].append(name+' '+stage[name]['status'])
    if stage['last_attempt']['status'] in ('invalid','future'):stage['schema_errors'].append('Official registry attempt clock invalid or future-dated')
    if _impossible_success_order(stage['last_success'],stage['last_attempt']):stage['schema_errors'].append('Official registry success is later than its latest attempt')
    error=state.get('last_error');stage['error']=error[:600] if isinstance(error,str) else (None if error is None else repr(error)[:200])
    if error is not None and not isinstance(error,str):stage['schema_errors'].append('Official registry error malformed')
    elif error:stage['failed_count']=1;stage['problems'].append('Official registry latest fetch failed')
    summary=state.get('last_summary')
    if not _batch_summary_valid(summary,('government_records_in_region','published_registry_leads')) or summary.get('published_registry_leads',0)>summary.get('government_records_in_region',0):
        stage['schema_errors'].append('Official registry counts missing or invalid')
    else:stage['records_in_region']=summary['government_records_in_region'];stage['published_leads']=summary['published_registry_leads']
    if not isinstance(state.get('seen'),dict):stage['schema_errors'].append('Official registry observation map missing or invalid')
    elif 'records_in_region' in stage and len(state['seen'])!=stage['records_in_region']:stage['schema_errors'].append('Official registry record count disagrees with observation map')
    if 'consecutive_failures' in state and (not _count(state['consecutive_failures']) or (state['consecutive_failures']>0 and not error)):
        stage['schema_errors'].append('Official registry failure count inconsistent')
    stage['problems'].extend(stage['schema_errors'])
    if not stage['problems']:stage['successful_count']=1
    return _summary(stage)


def _manual(state,queue,now):
    stage={'required':False,'healthy':None,'status':'manual_only','automatic_ingestion':False,
           'last_task_generated':state.get('last_run') if isinstance(state,dict) else None,
           'last_week':state.get('last_week') if isinstance(state,dict) else None,
           'note':'CPSO/CNO checking is a human task, not an automated registry scan. No task date is not a failed fetch.',
           'problems':[]}
    if not isinstance(state,dict):stage['problems'].append('Manual audit state unavailable or malformed')
    elif state.get('last_run') is not None and clock(state['last_run'],now)['status'] in ('invalid','future'):stage['problems'].append('Manual task date invalid or future-dated')
    if isinstance(state,dict) and state.get('last_week') is not None:
        try:
            match=re.fullmatch(r'(\d{4})-W(\d{2})',state['last_week'])
            if not match or dt.date.fromisocalendar(int(match[1]),int(match[2]),1)>now.date():raise ValueError()
        except (TypeError,ValueError):stage['problems'].append('Manual task week invalid or future-dated')
    if not isinstance(queue,dict) or not isinstance(queue.get('items'),list):stage['problems'].append('Manual audit queue unavailable or malformed')
    else:
        if any(not isinstance(x,dict) for x in queue['items']):stage['problems'].append('Manual audit queue item malformed')
        else:stage['pending_tasks']=sum(x.get('review_status')=='pending' for x in queue['items'])
    if stage['problems']:stage['status']='manual_state_invalid'
    return stage


def _strict_batch(stage,state,expected,now,directories=False):
    """Require records from this completed batch, without inventing precision.

    Source batches can include archived URLs outside the active view. Their
    declared failures therefore apply to batch integrity, not active failure
    counts. Only directory configuration has an exact expected batch scope.
    """
    sources=state.get('sources',{}) if isinstance(state,dict) else {}
    if not isinstance(sources,dict):sources={}
    summary=state.get('last_summary',{}) if isinstance(state,dict) else {}
    run=clock(state.get('last_run'),now) if isinstance(state,dict) else clock(None,now)
    issues=[];missing=outdated=unbound=0
    for ident,meta in expected.items():
        rec=sources.get(ident)
        if not isinstance(rec,dict):continue
        attempt=clock(rec.get('last_attempt'),now)
        if attempt['status']=='missing':missing+=1
        elif (attempt.get('age_hours_min') is not None and run.get('age_hours_max') is not None
              and attempt['age_hours_min']>run['age_hours_max']):outdated+=1
        if directories:
            signature=hashlib.sha256(json.dumps({k:meta.get(k) for k in ('url','mode')},sort_keys=True).encode()).hexdigest()
            if rec.get('source_signature')!=signature:unbound+=1
    stage['missing_attempt_count']=missing;stage['outdated_batch_attempt_count']=outdated
    if missing:issues.append(f'{missing} source records lack latest-attempt metadata')
    if outdated:issues.append(f'{outdated} source attempts predate the reported batch')
    if directories:
        stage['unverified_source_binding_count']=unbound
        if unbound:issues.append(f'{unbound} directory records lack a matching current URL/mode signature')
    if isinstance(summary,dict) and _count(summary.get('failed')):
        stage['declared_batch_failed_count']=summary['failed']
        if summary['failed']:issues.append(f"Latest batch declares {summary['failed']} failed checks; batch is not fully healthy")
        # Exact directory scope permits accounting consistency; source batches
        # may contain archived records and are intentionally not equated here.
        if directories and not missing and not outdated and all(isinstance(sources.get(k),dict) for k in expected):
            failures=sum(bool(sources[k].get('last_error')) for k in expected)
            if summary['failed']!=failures:issues.append('Directory batch failure count disagrees with source records')
        elif not directories:
            known_failures=sum(bool(sources[k].get('last_error')) for k in expected if isinstance(sources.get(k),dict))
            if summary['failed']<known_failures:issues.append('Source batch declares fewer failures than this coverage subset')
    stage['problems'].extend(issues)
    return _summary(stage)


def assess_all(db,source_state,now,discovery_sources,directory_config,directory_state,news_config,news_state,registry_state,manual_state,manual_queue):
    """All-stage read-only view; no optional AI or manual audit scan is required."""
    result=assess(db,source_state,now)
    stages={}
    try:evidence=_evidence_urls(db);err=[]
    except (ValueError,TypeError,KeyError) as exc:evidence=[];err=[str(exc)]
    stages['clinic_evidence']=_coverage({u:{'url':u} for u in evidence},source_state,now,config_errors=err)
    try:discovery=_urls(discovery_sources);err=[]
    except (ValueError,TypeError,KeyError) as exc:discovery=[];err=[str(exc)]
    stages['discovery_pages']=_coverage({u:{'url':u} for u in discovery},source_state,now,config_errors=err)
    stages['discovery_pages']['overlapping_evidence_urls']=len(set(discovery)&set(evidence))
    ss=source_state.get('last_summary') if isinstance(source_state,dict) else None
    if not _batch_summary_valid(ss,('urls','success','failed')) or ss['success']+ss['failed']!=ss['urls'] or ss['urls']<len(set(evidence)|set(discovery)):
        for key in ('clinic_evidence','discovery_pages'):
            stages[key]['schema_errors'].append('Source last-run counts missing, invalid or config changed')
            stages[key]['problems'].append('Source last-run counts missing, invalid or config changed');_summary(stages[key])
    expected={};errors=[]
    if not isinstance(directory_config,list) or not directory_config:errors.append('Directory configuration missing or empty')
    else:
        for item in directory_config:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'] or item['id'] in expected or not isinstance(item.get('url'),str) or item.get('mode') not in ('news','table','people','cards','healthline','page') or not _https(item['url']):errors.append('Invalid or duplicate directory configuration');continue
            expected[item['id']]={k:item[k] for k in ('url','name','mode') if k in item}
    stages['directories']=_coverage(expected,directory_state,now,directories=True,config_errors=errors)
    ds=directory_state.get('last_summary') if isinstance(directory_state,dict) else None
    if not _batch_summary_valid(ds,('sources','success','failed')) or ds['success']+ds['failed']!=ds['sources'] or ds['sources']!=len(expected):
        stages['directories']['schema_errors'].append('Directory last-run counts missing, invalid or config changed')
        stages['directories']['problems'].append('Directory last-run counts missing, invalid or config changed');_summary(stages['directories'])
    for key,urls in (('clinic_evidence',evidence),('discovery_pages',discovery)):
        _strict_batch(stages[key],source_state,{u:{'url':u} for u in urls},now)
    _strict_batch(stages['directories'],directory_state,expected,now,directories=True)
    stages['news_discovery']=_news(news_config,news_state,now)
    stages['official_registry']=_registry(registry_state,now)
    stages['professional_registry_audit']=_manual(manual_state,manual_queue,now)
    automated_ok=all(stage['healthy'] for stage in stages.values() if stage['required'])
    labels={'clinic_evidence':'Current clinic evidence pages','discovery_pages':'Configured discovery pages','directories':'Regional directories','news_discovery':'Rotating news discovery','official_registry':'Ontario government registry','professional_registry_audit':'Manual CPSO/CNO audit'}
    for key,stage in stages.items():stage['label']=labels[key]
    problems=[key+': '+problem for key,stage in stages.items() for problem in stage['problems']]
    result.update(health_scope='all_automated_stages_and_manual_metadata',automated_stages_healthy=automated_ok,stages=stages,healthy=not problems,problems=problems,
                  status='healthy' if not problems else ('degraded' if any(s.get('successful_count',0) for s in stages.values()) else 'unavailable'),
                  optional_ai={'required':False,'status':'not_assessed','note':'AI triage is optional and not required for deterministic monitoring.'},
                  manual_warnings=stages['professional_registry_audit']['problems'],
                  freshness_policy={'hours':MAX_AGE_HOURS,'date_only':'age interval; uncertain boundary is not healthy'})
    return bounded_details(result)


def bounded_details(result,limit=48000):
    """Keep heartbeat JSON below issue-body limits without truncating summaries.

    Counts/status/problems remain complete; only enumerated attention items may
    be omitted, with explicit per-list truncation counts.
    """
    lists=[('failed_sources',result.get('failed_sources',[]))]+[(key+'.items',stage.get('items',[])) for key,stage in result['stages'].items()]
    original={key:len(items) for key,items in lists}
    result['detail_truncation']={}
    while len(json.dumps(result,indent=2))>limit and any(items for _,items in lists):
        key,items=max(lists,key=lambda pair:len(pair[1]))
        items.pop()
        result['detail_truncation'][key]={'total':original[key],'shown':len(items),'omitted':original[key]-len(items)}
    return result


def current():
    names=('clinics','source_state','discovery_sources','curated_directories','directory_state','search_queries','discovery_state','official_registry_state','registry_audit_state','registry_audit_queue')
    values={};load_errors={}
    for name in names:
        try:values[name]=json.loads((ROOT/'data'/f'{name}.json').read_text(),parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))
        except (OSError,ValueError,UnicodeError) as exc:values[name]=None;load_errors[name]={'category':type(exc).__name__,'error':'State/config file unavailable or invalid'}
    result=assess_all(values['clinics'],values['source_state'],dt.datetime.now(UTC),values['discovery_sources'],values['curated_directories'],values['directory_state'],values['search_queries'],values['discovery_state'],values['official_registry_state'],values['registry_audit_state'],values['registry_audit_queue'])
    result['state_load_errors']=load_errors
    return result


if __name__=='__main__':
    result=current()
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['healthy'] else 1)
