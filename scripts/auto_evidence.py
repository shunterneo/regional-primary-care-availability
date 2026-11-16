"""Conservative, versioned evidence candidates for reviewed single-office sources.

Publication remains paused. This bounded grammar is not a general-language truth
checker. Any context ambiguity is a review lead, never an automatic intake claim.
"""
from __future__ import annotations
import hashlib, json, re
from datetime import date, datetime, timezone
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

EVIDENCE_VERSION = 'context-v2'
PUBLICATION_TEXT_LIMIT = 30000
WHO = r"(?:we\s+(?:are|\'re)|our\s+(?:(?:family|primary\s+care)\s+)?(?:clinic|practice|office)\s+(?:is|are)|this\s+(?:(?:family|primary\s+care)\s+)?(?:clinic|practice|office)\s+(?:is|are))"
ACCEPT = re.compile(r"\b"+WHO+r"\s+(?:currently\s+|now\s+)?(?:accepting|taking|enrolling|registering|welcoming)\s+(?:applications\s+from\s+)?new\s+(?:family\s+medicine\s+)?(?:patients?|clients?)\b", re.I)
CLOSED = re.compile(r"\b"+WHO+r"\s+(?:(?:currently|now)\s+)?(?:not\s+|no\s+longer\s+|unable\s+to\s+|isn['’]t\s+|aren['’]t\s+)(?:accepting|taking|enrolling|registering|welcoming)\s+new\s+(?:patients?|clients?)\b", re.I)
CLOSED2 = re.compile(r"\b(?:we|our\s+(?:clinic|practice|office)|this\s+(?:clinic|practice|office))\s+(?:are\s+|is\s+)?(?:no\s+longer|not\s+currently|not)\s+(?:accepting|taking|enrolling|registering)\s+new\s+(?:patients?|clients?)\b", re.I)
PERMANENT = re.compile(r"\b(?:our|this)\s+(?:clinic|practice|office|location)\s+(?:is|has\s+been)\s+(?:now\s+)?permanently\s+closed\b|\bwe\s+have\s+permanently\s+closed\s+(?:our|this)\s+(?:clinic|practice|office|location)\b", re.I)
# Examine the COMPLETE context, not only the sentence containing a positive verb.
UNSAFE = re.compile(r"\b(?:some|selected|certain|may|might|could|would|should|if|unless|whether|assuming|wait\s?list|waiting\s+list|eligible|eligibility|only|limited|by\s+referral|must|required|requirements?|subject\s+to|aged|catchment|residents?|expired|suspended|suspension|historically|previously|archive[ds]?|last\s+year|used\s+to|temporarily|except|not\s+all|for\s+example|example\s+(?:wording|statement|notice)|sample\s+(?:wording|statement|notice)|template|hypothetical|quotation|quoted|starting|beginning|effective|will|soon|tomorrow|next\s+(?:week|month|year)|moved|moving|relocat(?:ed|ion|ing)|reopen(?:ed|ing)?|other\s+(?:clinic|practice|office|location)|locations|branches)\b", re.I)
DATED = re.compile(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\bas\s+of\b", re.I)
GENERIC_NO = re.compile(r"\b(?:not|no\s+longer|unable\s+to|cannot)\s+(?:currently\s+)?(?:accepting|taking|enrolling|registering|welcoming)\s+(?:any\s+)?new\s+(?:family\s+medicine\s+)?(?:patients?|clients?)\b|\bclosed\s+to\s+new\s+(?:patients?|clients?)\b", re.I)
GENERIC_YES = re.compile(r"\b(?:accepting|taking|enrolling|registering|welcoming)\s+(?:applications\s+from\s+)?new\s+(?:family\s+medicine\s+)?(?:patients?|clients?)\b", re.I)
THIRD_PARTY = ('211ontario.ca','thehealthline.ca','google.com','news.google.com','ontario.ca','cpso.on.ca','facebook.com','instagram.com','finddoc.ca','waitlistwise.ca','cityofwoodstock.ca')


def host(url):
    try: return (urlsplit(url or '').hostname or '').lower().removeprefix('www.')
    except (TypeError, ValueError): return ''


def https_url(url):
    try:
        parsed = urlsplit(url or '')
        return parsed.scheme == 'https' and bool(parsed.hostname) and not parsed.username and not parsed.password
    except (TypeError, ValueError): return False


def scope_identity(clinic):
    """Bind an office-source review to exact identity and care-model facts."""
    fields = ('id','name','community','address','clinic_url','evidence_url','care_model','clinic_type')
    return hashlib.sha256(json.dumps({key:clinic.get(key) for key in fields},sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def scope_fingerprint(clinic):
    """A changed/re-reviewed scope must collect fresh observations."""
    return hashlib.sha256(json.dumps(clinic.get('auto_publication_scope'),sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def first_party(clinic, url, owners, final_url=None, today=None):
    """Require reviewed single-office source identity, not merely matching hosts."""
    if clinic.get('auto_updates_enabled') is False: return False
    if clinic.get('clinic_type') == 'FHT' and clinic.get('auto_updates_enabled') is not True: return False
    if clinic.get('operating_status') in ('closed','archived'): return False
    if owners != [clinic.get('id')] or clinic.get('evidence_url') != url: return False
    h = host(url)
    if not https_url(url) or not https_url(clinic.get('clinic_url')): return False
    if h != host(clinic.get('clinic_url')) or any(h==d or h.endswith('.'+d) for d in THIRD_PARTY): return False
    if final_url is not None:
        if not https_url(final_url) or host(final_url) != h: return False
        original, final = urlsplit(url), urlsplit(final_url)
        # A same-host redirect may be another office. Canonical path changes
        # need a new source-scope review, not automatic attribution.
        if (original.path.rstrip('/') != final.path.rstrip('/') or original.query != final.query): return False
    scope = clinic.get('auto_publication_scope')
    if not isinstance(scope, dict): return False
    if (type(scope.get('version')) is not int or scope['version'] != 1 or
        scope.get('identity_hash') != scope_identity(clinic) or scope.get('clinic_id') != clinic.get('id') or
        scope.get('source_url') != url or scope.get('scope') != 'single_office' or
        scope.get('method') != 'independent_public_source_review' or
        not isinstance(scope.get('context_template_hash'),str) or
        not re.fullmatch(r'[0-9a-f]{64}',scope['context_template_hash']) or
        not isinstance(scope.get('evidence'), str) or not scope['evidence'].strip()): return False
    try:
        checked = date.fromisoformat(scope['reviewed_on'])
        current = date.fromisoformat(today) if isinstance(today, str) else (today or datetime.now(timezone.utc).date())
        if checked > current: return False
    except (KeyError, TypeError, ValueError): return False
    return True


def publication_text(html):
    """Preserve complete headings/paragraphs; never truncate into a positive claim.

    Explicitly hidden/non-rendered text cannot supply a claim or contradiction.
    CSS/JavaScript-dependent pages still require a separately reviewed adapter.
    """
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    dated_metadata = [node.get('content','') for node in soup.find_all('meta')
                      if re.search(r'date|published|modified', str(node.get('property') or node.get('name') or ''), re.I)]
    if soup.find('meta', attrs={'http-equiv': re.compile('refresh', re.I)}): return None
    # This adapter supports static text only. A browser/rendered-source adapter
    # must separately review external CSS, executable JS and collapsed content.
    if any('stylesheet' in ' '.join(node.get('rel',[])).lower() for node in soup.find_all('link')): return None
    if any(any(key.lower().startswith('on') for key in node.attrs) for node in soup.find_all(True)): return None
    if any(str(node.get('href','')).strip().lower().startswith('javascript:') for node in soup.find_all(True)): return None
    if soup.find(['img','picture','iframe','object','embed','canvas','video','audio','svg']): return None
    if any(node.get_text(' ',strip=True) for node in soup.find_all('noscript')): return None
    if any(node.get('src') or (node.get_text().strip() and node.get('type','').lower() not in ('application/json','application/ld+json')) for node in soup.find_all('script')): return None
    if any(node.get_text().strip() for node in soup.find_all('style')): return None
    if any(node.get('style','').strip() for node in soup.find_all(True)): return None
    if any(not node.has_attr('open') and node.get_text(' ',strip=True) for node in soup.find_all(['details','dialog'])): return None
    # Static extraction cannot reliably resolve stylesheet visibility/cascades.
    # Do not manufacture a visible claim from class-hidden/struck-out notices.
    if any(node.get_text(' ',strip=True) for node in soup.find_all(['del','s'])): return None
    for node in list(soup.find_all(True)):
        if node.parent is None: continue
        # aria-hidden changes accessibility exposure, not visual visibility.
        # Treat meaningful text under it as ambiguous rather than deleting it.
        if str(node.get('aria-hidden','')).lower()=='true' and node.get_text(' ',strip=True): return None
        style = re.sub(r'\s+', '', node.get('style', '')).lower()
        if (node.name in ('script','style','noscript','template','svg','head') or
            node.has_attr('hidden') or
            'display:none' in style or 'visibility:hidden' in style): node.decompose()
    office_headings = [node.get_text(' ',strip=True) for node in soup.find_all(['h1','h2','h3','h4'])
                       if re.search(r'\b(?:clinic|practice|office|location|centre|center|branch)\b', node.get_text(' ',strip=True), re.I)]
    if len(set(office_headings)) > 1: return None
    # Mark quotations before extracting text; quotes cannot become self-assertions.
    for node in soup.find_all(['blockquote','q']): node.insert_before('\nQUOTED CONTENT: ')
    for node in soup.find_all('br'): node.replace_with('\n')
    for node in soup.find_all(['p','div','section','article','li','h1','h2','h3','h4','h5','h6','tr','header','footer','nav','form']):
        node.insert_before('\n'); node.insert_after('\n')
    text = '\n'.join(' '.join(line.split()) for line in [title,*dated_metadata,*soup.get_text().splitlines()] if line.strip())
    if not text or len(text) > PUBLICATION_TEXT_LIMIT: return None
    return text


def decisive_statement(context, observed_on=None):
    """Recognize only unambiguous bounded assertions within COMPLETE context.

    Dated material is deliberately review-only, even if its date is recent;
    fetching a historical or future notice twice is not current verification.
    """
    if not isinstance(context, str) or not context.strip() or len(context) > PUBLICATION_TEXT_LIMIT: return None
    context = '\n'.join(' '.join(line.split()) for line in context.splitlines() if line.strip())
    if UNSAFE.search(context) or DATED.search(context) or re.search('["“”]|[‘‚].*?[’]', context): return None
    lines = [line.strip() for raw in context.splitlines() for line in re.split(r'(?<=[.!?])\s+',raw) if line.strip()]
    found = []
    for sentence in lines:
        value = sentence.rstrip('.!?').strip()
        tail = r'(?:\s+for\s+(?:ongoing\s+primary\s+care|primary\s+care|ongoing\s+care|family\s+medicine))?'
        exact = lambda rule: bool(re.fullmatch('(?:'+rule.pattern+')'+tail,value,re.I))
        yes = exact(ACCEPT); no = exact(CLOSED) or exact(CLOSED2); permanent = bool(PERMANENT.fullmatch(value))
        # Never delete arbitrary prefixes/qualifiers as if they were the claim.
        if (ACCEPT.search(sentence) or CLOSED.search(sentence) or CLOSED2.search(sentence) or PERMANENT.search(sentence)) and not (yes or no or permanent): return None
        if sum((yes,no,permanent)) > 1: return None
        # No truncating long sentences before examining their qualifications.
        if (yes or no or permanent) and len(sentence)>320: return None
        if permanent: found.append(('closed',sentence))
        elif no: found.append(('not_accepting',sentence))
        elif yes: found.append(('accepting',sentence))
    if not found or len(found)>2 or len({status for status,_ in found}) != 1: return None
    status, quote = found[0]
    has_negative = bool(GENERIC_NO.search(context))
    unnegated_context = GENERIC_NO.sub('',context)
    if re.search(r"\b(?:not|never|no|cannot|isn['’]t|aren['’]t|wrong|false|incorrect|outdated|superseded|cancelled|canceled|withdrawn)\b", unnegated_context, re.I): return None
    has_positive = bool(GENERIC_YES.search(unnegated_context))
    if status=='accepting' and has_negative: return None
    if status in ('not_accepting','closed') and has_positive: return None
    if status != 'closed' and PERMANENT.search(context): return None
    template = context
    for _, assertion in found: template = template.replace(assertion,'[OFFICE_INTAKE_ASSERTION]')
    return {'status':status,'quote':quote,'rule_version':EVIDENCE_VERSION,
            'context_hash':hashlib.sha256(context.encode()).hexdigest(),
            'template_hash':hashlib.sha256(template.encode()).hexdigest()}


def publication_candidate(html):
    """Bind the reviewed template to DOM/attributes as well as visible text.

    Changed paths, accessibility labels, attributes or layout cannot silently
    inherit a plain-text approval. Rich/rendered sources need another adapter.
    """
    candidate = decisive_statement(publication_text(html))
    if not candidate: return None
    soup = BeautifulSoup(html, 'html.parser')
    structure = [(node.name, sorted((key,value) for key,value in node.attrs.items()))
                 for node in soup.find_all(True)]
    candidate['template_hash'] = hashlib.sha256(json.dumps(
        {'text_template':candidate['template_hash'],'structure':structure},
        sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return candidate


def explicit_longitudinal(quote):
    if not quote: return False
    if re.search(r'\b(?:walk[- ]?in|same[- ]?day|urgent)\s+(?:patients?|visits?|appointments?)\b',quote,re.I): return False
    return bool(re.search(r'\b(?:family\s+(?:practice|physician|doctor|medicine|patients?)|primary\s+care|ongoing\s+care|long[- ]term\s+care|roster(?:ed|ing)?|enrol(?:led|lment|ment)?)\b',quote,re.I))


def valid_candidate(candidate):
    return (isinstance(candidate,dict) and candidate.get('rule_version')==EVIDENCE_VERSION and
        candidate.get('status') in ('accepting','not_accepting','closed') and
        isinstance(candidate.get('quote'),str) and bool(candidate['quote'].strip()) and
        isinstance(candidate.get('context_hash'),str) and
        bool(re.fullmatch(r'[0-9a-f]{64}',candidate['context_hash'])) and
        isinstance(candidate.get('template_hash'),str) and
        bool(re.fullmatch(r'[0-9a-f]{64}',candidate['template_hash'])))


def observe(prev, candidate, now, scope_hash=None):
    """Version/context changes or invalid state start a fresh two-day sequence."""
    if not valid_candidate(candidate) or not isinstance(scope_hash,str) or not re.fullmatch(r'[0-9a-f]{64}',scope_hash): return {}
    candidate = {**candidate,'scope_hash':scope_hash}
    try:
        stamp = datetime.fromisoformat(now.replace('Z','+00:00'))
        if stamp.tzinfo is None: return {}
        day = stamp.astimezone(timezone.utc).date().isoformat()
    except (AttributeError,TypeError,ValueError): return {}
    fields = ('status','quote','rule_version','context_hash','template_hash','scope_hash')
    fresh = {key:candidate[key] for key in fields}
    fresh.update(first_seen=now,last_seen=now,days=[day])
    if not isinstance(prev,dict) or any(prev.get(key)!=candidate[key] for key in fields): return fresh
    days = prev.get('days',[])
    try:
        parsed = [date.fromisoformat(d) for d in days]
        if (not parsed or parsed != sorted(set(parsed)) or
            any(not 0 <= (parsed[i]-parsed[i-1]).days <= 4 for i in range(1,len(parsed))) or
            not 0 <= (date.fromisoformat(day)-parsed[-1]).days <= 4): return fresh
        prior_stamp = datetime.fromisoformat(prev['last_seen'].replace('Z','+00:00'))
        if prior_stamp.tzinfo is None or prior_stamp > stamp or prior_stamp.astimezone(timezone.utc).date() != parsed[-1]: return fresh
    except (AttributeError,KeyError,TypeError,ValueError): return fresh
    days = list(days)
    if day not in days: days.append(day)
    return {**prev,**{key:candidate[key] for key in fields},'last_seen':now,'days':days[-3:]}


def confirmed(obs, today):
    if not valid_candidate(obs) or not isinstance(obs.get('scope_hash'),str) or not re.fullmatch(r'[0-9a-f]{64}',obs['scope_hash']): return False
    try:
        current = date.fromisoformat(today)
        days = [date.fromisoformat(d) for d in obs['days']]
        if len(days)<2 or days != sorted(set(days)): return False
        if any(not 1 <= (days[i]-days[i-1]).days <= 4 for i in range(1,len(days))): return False
        last = datetime.fromisoformat(obs['last_seen'].replace('Z','+00:00'))
        first = datetime.fromisoformat(obs['first_seen'].replace('Z','+00:00'))
        if last.tzinfo is None or first.tzinfo is None or first>last: return False
        if last.astimezone(timezone.utc).date()!=days[-1]: return False
        return 0 <= (current-days[-1]).days <= 1
    except (AttributeError,KeyError,TypeError,ValueError): return False
