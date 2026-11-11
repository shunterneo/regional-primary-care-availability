"""Strict, deterministic, first-party-only evidence for automatic publication.

Never infer intake from application buttons, third-party listings, AI output or
missing sites. A classification is only a candidate until observed on two
separate days by the monitoring workflow.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from collections import Counter

# Explicit, self-referential clinic assertions. Narrow by design: uncertain
# announcements remain in the human review queue.
WHO = r"(?:we\s+(?:are|\'re)|our\s+(?:(?:family|primary\s+care)\s+)?(?:clinic|practice|office)\s+(?:is|are)|this\s+(?:(?:family|primary\s+care)\s+)?(?:clinic|practice|office)\s+(?:is|are))"
ACCEPT = re.compile(r"\b"+WHO+r"\s+(?:currently\s+|now\s+)?(?:accepting|taking|enrolling|registering|welcoming)\s+(?:applications\s+from\s+)?new\s+(?:family\s+medicine\s+)?(?:patients?|clients?)\b",re.I)
CLOSED = re.compile(r"\b"+WHO+r"\s+(?:(?:currently|now)\s+)?(?:not\s+|no\s+longer\s+|unable\s+to\s+|isn['’]t\s+|aren['’]t\s+)(?:accepting|taking|enrolling|registering|welcoming)\s+new\s+(?:patients?|clients?)\b",re.I)
# Broader negative grammar: "We are no longer accepting new patients".
CLOSED2 = re.compile(r"\b(?:we|our\s+(?:clinic|practice|office)|this\s+(?:clinic|practice|office))\s+(?:are\s+|is\s+)?(?:no\s+longer|not\s+currently|not)\s+(?:accepting|taking|enrolling|registering)\s+new\s+(?:patients?|clients?)\b",re.I)
PERMANENT = re.compile(r"\b(?:our|this)\s+(?:clinic|practice|office|location)\s+(?:is|has\s+been)\s+(?:now\s+)?permanently\s+closed\b|\bwe\s+have\s+permanently\s+closed\s+(?:our|this)\s+(?:clinic|practice|office|location)\b",re.I)
UNSAFE = re.compile(r"\b(?:some|selected|certain|may|might|could|wait\s?list|waiting\s+list|eligible|eligibility|only|limited|certain\s+locations|certain\s+physicians|by\s+referral|historically|previously|last\s+year|used\s+to|temporarily|except|not\s+all)\b",re.I)
THIRD_PARTY = ('211ontario.ca','thehealthline.ca','google.com','news.google.com','ontario.ca','cpso.on.ca','facebook.com','instagram.com','finddoc.ca','waitlistwise.ca','cityofwoodstock.ca')

def host(url):
    try:
        return urlsplit(url).hostname.lower().removeprefix('www.')
    except Exception:
        return ''

def first_party(clinic, url, owners, final_url=None):
    """Require one clinic per evidence URL, same publisher as clinic home."""
    if clinic.get('auto_updates_enabled') is False:return False
    # A team-wide page may not apply to an individual physician/location.
    if clinic.get('clinic_type')=='FHT' and clinic.get('auto_updates_enabled') is not True:return False
    if clinic.get('operating_status') in ('closed','archived'):return False
    if owners != [clinic.get('id')]: return False
    if clinic.get('evidence_url') != url:return False
    h=host(url);site_host=host(clinic.get('clinic_url',''))
    if not h or h != site_host or any(h==d or h.endswith('.'+d) for d in THIRD_PARTY):return False
    if final_url and host(final_url)!=h:return False
    return True

def decisive_statement(excerpt):
    """One unambiguous first-person claim on a first-party office page."""
    lines=[]
    for item in excerpt.splitlines():
        lines.extend(re.split(r'(?<=[.!?])\s+',item.strip()))
    found=[]
    for raw in lines:
        s=' '.join(raw.split())[:500]
        if not s:continue
        yes=bool(ACCEPT.search(s));no=bool(CLOSED.search(s) or CLOSED2.search(s));perm=bool(PERMANENT.search(s))
        if yes and (no or UNSAFE.search(s)):return None
        if no and UNSAFE.search(s):return None
        if perm and UNSAFE.search(s):return None
        if perm:found.append(('closed',s))
        elif no:found.append(('not_accepting',s))
        elif yes:found.append(('accepting',s))
    if not found:return None
    if len(set(x[0] for x in found))!=1:return None
    # Avoid publishing a snippet of generic how-to or FAQ wording.
    if len(found)>2:return None
    return {'status':found[0][0],'quote':found[0][1][:320]}

def explicit_longitudinal(quote):
    """Require family/NP ongoing care in the SAME claim; walk-in booking never suffices."""
    if not quote:return False
    if re.search(r'\b(?:walk[- ]?in|same[- ]?day|urgent)\s+(?:patients?|visits?|appointments?)\b',quote,re.I):return False
    return bool(re.search(r'\b(?:family\s+(?:practice|physician|doctor|medicine|patients?)|primary\s+care|ongoing\s+care|long[- ]term\s+care|roster(?:ed|ing)?|enrol(?:led|lment|ment)?)\b',quote,re.I))

def observe(prev, candidate, now):
    """Two observations on distinct days, within 4 days of each other."""
    from datetime import datetime
    if not candidate:return {}
    day=now[:10]
    if prev.get('status')!=candidate['status'] or prev.get('quote')!=candidate['quote']:
        return {'status':candidate['status'],'quote':candidate['quote'],'first_seen':now,'last_seen':now,'days':[day]}
    days=list(prev.get('days',[]))
    if days:
        try:
            gap=(datetime.fromisoformat(day).date()-datetime.fromisoformat(days[-1]).date()).days
        except (TypeError,ValueError):gap=100
        if gap>4 or gap<0:days=[]
    if day not in days:days.append(day)
    return {**prev,'status':candidate['status'],'quote':candidate['quote'], 'last_seen':now,'days':days[-3:]}

def confirmed(obs, today):
    from datetime import date
    if len(obs.get('days',[]))<2:return False
    try:return (date.fromisoformat(today)-date.fromisoformat(obs['days'][-1])).days<=1
    except (ValueError,KeyError):return False
