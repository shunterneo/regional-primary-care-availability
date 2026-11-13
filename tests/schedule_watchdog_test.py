import sys,pathlib,datetime as dt
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from check_schedule import assess
now=dt.datetime.fromisoformat('2026-11-13T15:18:00+00:00')
assert not assess([],now)['healthy']
assert assess([],now-dt.timedelta(hours=1))['healthy']
r={'created_at':'2026-11-13T13:30:00Z','event':'push','status':'completed','conclusion':'success','html_url':'test'}
assert not assess([r],now)['healthy']
r['event']='schedule';assert assess([r],now)['healthy']
r['conclusion']='failure';assert not assess([r],now)['healthy']
print('PASS: missed schedule after grace, push excluded, successful scheduled run accepted, failure reported')
