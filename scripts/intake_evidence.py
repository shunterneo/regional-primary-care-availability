"""Conservative heuristic review labels for public clinic pages.

These labels are *proposals*, not proof of enrollment and never change a clinic status.
"""
from __future__ import annotations
import re

CLOSED = re.compile(r"\b(?:not|no longer|currently not|aren['’]t|isn['’]t|unable to|cannot)\s+(?:currently\s+)?(?:accepting|taking|registering|enrolling|rostering)\s+(?:any\s+)?new\s+(?:patients?|clients?|applications?)\b|\bclosed\s+to\s+new\s+(?:patients?|applications?)\b", re.I)
OPEN = re.compile(r"\b(?:currently\s+)?(?:now\s+)?(?:accepting|taking|registering|enrolling|rostering|welcoming)\s+(?:new\s+)?(?:patient|client|applicant)(?:s|\s+applications?)?\b|\bnew[ -]patient\s+(?:registration|applications?)\s+(?:is\s+)?(?:open|available)\b", re.I)
WAITLIST = re.compile(r"\bwait\s?list|waiting\s+list|attachment\s+queue", re.I)
LIMITED = re.compile(r"\blimited\s+(?:intake|capacity|spots?|availability)|eligib(?:le|ility)|by\s+referral\s+only|residents\s+only", re.I)


def classify(excerpt: str) -> dict:
    """Returns possible category and matching short excerpts; ambiguity returns needs_review."""
    lines = [re.sub(r'\s+', ' ', s).strip() for raw in excerpt.splitlines() for s in re.split(r'(?<=[.!?])\s+', raw) if s.strip()]
    found = {'possible_closed': [], 'possible_accepting': [], 'possible_waitlist': [], 'possible_limited': []}
    for line in lines:
        line = line[:450]
        # Check negative expressions first to avoid falsely parsing "not accepting" as open.
        if CLOSED.search(line): found['possible_closed'].append(line)
        elif OPEN.search(line): found['possible_accepting'].append(line)
        if WAITLIST.search(line): found['possible_waitlist'].append(line)
        if LIMITED.search(line): found['possible_limited'].append(line)
    active = [k for k,v in found.items() if v]
    if not active: return {'classification':'unclear','excerpts':[],'confidence':'insufficient'}
    if len(active)>1: return {'classification':'conflicting_or_conditional','excerpts':list(dict.fromkeys(sum([found[k] for k in active],[])))[:3],'confidence':'needs_human_review'}
    return {'classification':active[0],'excerpts':found[active[0]][:3],'confidence':'text_match_only'}
