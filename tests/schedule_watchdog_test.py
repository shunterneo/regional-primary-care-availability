import sys,pathlib,datetime as dt
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from check_schedule import assess
now=dt.datetime.fromisoformat('2026-11-13T15:18:00+00:00')
assert not assess([],now)['healthy']
assert assess([],now-dt.timedelta(hours=1))['healthy']
r={'created_at':'2026-11-13T13:30:00Z','run_started_at':'2026-11-13T13:30:00Z','event':'push','status':'completed','conclusion':'success','html_url':'test'}
assert not assess([r],now)['healthy']
r['event']='schedule';assert assess([r],now)['healthy']
r['conclusion']='failure';assert not assess([r],now)['healthy']
print('PASS: missed schedule after grace, push excluded, successful scheduled run accepted, failure reported')

# The overnight window must not hide the previous day's unmet obligation.
assert not assess([],dt.datetime.fromisoformat('2026-11-14T05:10:00+00:00'))['healthy']
r.update(created_at='2026-11-13T21:47:09Z',run_started_at='2026-11-13T21:47:09Z',conclusion='success')
late=assess([r],dt.datetime.fromisoformat('2026-11-14T05:10:00+00:00'))
assert not late['healthy'] and late['late_start'] and late['start_delay_minutes']==510.15
# Future timestamps cannot satisfy the expected run.
r['created_at']='2026-11-15T13:30:00Z'
assert not assess([r],now)['healthy']
# Prior on-time completion survives local midnight; timezone/DST offset follows date.
r.update(created_at='2026-11-13T13:30:00Z',run_started_at='2026-11-13T13:30:00Z')
assert assess([r],dt.datetime.fromisoformat('2026-11-14T05:10:00+00:00'))['healthy']
assert assess([],dt.datetime.fromisoformat('2026-07-14T04:10:00+00:00'))['expected_start']=='2026-07-13T08:17:00-04:00'
print('PASS: overnight obligation, actual lateness, future timestamps and DST-aware schedule')

# Created before the deadline but started after it, or never confirmed started.
queued = dict(r, created_at='2026-11-13T13:20:00Z', run_started_at='2026-11-13T16:20:00Z')
check = assess([queued],dt.datetime.fromisoformat('2026-11-13T17:00:00+00:00'))
assert not check['healthy'] and check['late_start']
assert check['queue_delay_minutes']==3 and check['start_delay_minutes']==183
for changes in (dict(status='queued', run_started_at=queued['created_at']),
                dict(run_started_at=None),dict(run_started_at='garbage'),
                dict(run_started_at='2026-11-13T12:00:00Z')):
    report = assess([dict(queued, **changes)], now)
    assert not report['healthy'] and report['start_delay_minutes'] is None
print('PASS: queued timestamp, genuinely late start and invalid/missing start evidence distinguished')
