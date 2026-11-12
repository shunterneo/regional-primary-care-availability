from __future__ import annotations
import json, pathlib, datetime, math, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'clinics.json'
CARE_MODELS={
 'ongoing':'Ongoing family doctor / NP care',
 'both':'Family practice + walk-in',
 'walk_in_only':'Walk-in only (not patient attachment)',
 'unverified':'Care model not verified',
}

def ongoing_eligible(clinic):
    return clinic.get('care_model') in ('ongoing','both')

STATUSES={
 'accepting':('Applications advertised','accepting'),
 'reported':('Reported by regional source','reported'),
 'limited':('Limited intake / eligibility','limited'),
 'waitlist':('Waitlist / application queue','waitlist'),
 'not_accepting':('Not accepting (clinic notice)','closed'),
 'unknown':('Intake not confirmed','unknown'),
 'needs_review':('Needs reconfirmation','stale'),
}
CITY_COORDS={
'Tillsonburg':(42.8654,-80.7228),'Norwich':(42.9887,-80.5976),'Courtland':(42.8425,-80.6333),'Port Burwell':(42.6467,-80.8003),'Vienna':(42.6819,-80.7906),'Otterville':(42.9249,-80.6016),'Straffordville':(42.7496,-80.7748),'Delhi':(42.8525,-80.4989),'Aylmer':(42.7826,-80.9826),'Ingersoll':(43.0406,-80.8740),'Woodstock':(43.1372,-80.7378),'Simcoe':(42.8419,-80.3141),'Waterford':(42.9318,-80.2911),'Port Rowan':(42.6263,-80.4523),'London':(42.9849,-81.2453),'St. Thomas':(42.7781,-81.186),'Stratford':(43.3700,-80.9822),'Tavistock':(43.3206,-80.8351),'Brantford':(43.1394,-80.2644),'Cambridge':(43.3616,-80.3144),'Ayr':(43.2845,-80.4490),'Kitchener':(43.4516,-80.4925),'Waterloo':(43.4643,-80.5204),'Breslau':(43.4787,-80.4079),'Ilderton':(43.0745,-81.374),'Strathroy':(42.9555,-81.621),'Mount Brydges':(42.9090,-81.4820),'Ailsa Craig':(43.146,-81.535),'Paris':(43.194,-80.386),'Burford':(43.102,-80.426),'New Hamburg':(43.379,-80.711)}

# Additional towns require a verified public geographic point before publication.
extra_file=ROOT/'data'/'extra_communities.json'
if extra_file.exists():
    for _town,_point in json.loads(extra_file.read_text()).items():
        if isinstance(_point,list) and len(_point)==2:
            CITY_COORDS[_town]=tuple(_point)

def load_data():
    return json.loads(DATA.read_text(encoding='utf8'))

def effective_status(clinic, today):
    from evidence_policy import display_intake_status
    return display_intake_status(clinic, today)

def legacy_effective_status(clinic, today):
    status=clinic['status']
    if status=='unknown': return status
    # A stale enrolment statement is a prompt to reconfirm, not proof of closure.
    try: d=datetime.date.fromisoformat(clinic['last_reviewed'])
    except (KeyError, ValueError): return 'needs_review'
    max_age=30 if status in {'accepting','limited','not_accepting'} else 45
    if (today-d).days>max_age: return 'needs_review'
    return status

def km(lat1,lon1,lat2,lon2):
    R=6371
    a=math.sin(math.radians(lat2-lat1)/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(math.radians(lon2-lon1)/2)**2
    return R*2*math.atan2(math.sqrt(a),math.sqrt(max(0,1-a)))

def is_url(s): return bool(re.fullmatch(r'https://[^\s<>"\']+',s or ''))
