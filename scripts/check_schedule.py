"""Watch daily schedule execution, separately from source coverage/publication."""
import datetime as dt, json, sys
from zoneinfo import ZoneInfo

def assess(runs,now):
    local=now.astimezone(ZoneInfo('America/Toronto'))
    due=local.replace(hour=8,minute=17,second=0,microsecond=0)
    deadline=due+dt.timedelta(hours=2)
    current=[]
    for run in runs:
        if run.get('event')!='schedule':continue
        created=dt.datetime.fromisoformat(run['created_at'].replace('Z','+00:00')).astimezone(local.tzinfo)
        if created>=due:current.append(run)
    latest=max(current,key=lambda r:r['created_at']) if current else None
    problem=None
    if now>=deadline and latest is None:problem='No daily scheduled run observed after the expected start plus 2-hour grace period'
    elif latest and latest.get('status')=='completed' and latest.get('conclusion')!='success':problem='Latest daily scheduled run did not succeed'
    elif latest and latest.get('status')!='completed' and now-dt.datetime.fromisoformat(latest['created_at'].replace('Z','+00:00'))>dt.timedelta(hours=2):problem='Daily scheduled run has not completed within 2 hours'
    return {'checked_at':now.isoformat(),'expected_start':due.isoformat(),'grace_deadline':deadline.isoformat(),'latest_scheduled_run':latest.get('html_url') if latest else None,'healthy':problem is None,'problem':problem,'note':'Push/manual runs do not satisfy scheduled-run coverage. Scheduler delay cause is unknown.'}
if __name__=='__main__':
    result=assess(json.load(open(sys.argv[1]))['workflow_runs'],dt.datetime.now(dt.timezone.utc))
    print(json.dumps(result,indent=2));sys.exit(0 if result['healthy'] else 1)
