"""Read-only, escaped public research inbox. Never writes queues or clinic facts."""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import json
import re
from collections import Counter
from urllib.parse import urlsplit

from profile_integrity import public_https_url, office_address
from official_registry import existing_clinic, ROOT_URL as REGISTRY_URL

REPO_URL = 'https://github.com/shunterneo/regional-primary-care-availability'
GROUPS = {
    'source_change': 'Changed clinic sources',
    'discovery': 'News and directory leads',
    'registry_profile': 'Government profile observations',
    'manual_audit': 'Professional-register review tasks',
    'failure': 'Sources needing repair',
}
ERROR_ACTIONS = {
    'blocked_access': 'Access was denied. Keep the listing unchanged and review the official source; do not bypass access controls.',
    'blocked_page': 'The response was an access challenge, not clinic evidence. Leave status unchanged; no challenge bypass is attempted.',
    'login_required': 'The source requires sign-in. No authentication or private patient information is collected by this checker.',
    'render_required': 'This page needs a separately tested rendered-page adapter. A successful download of its app shell cannot verify intake.',
    'tls_error': 'HTTPS certificate verification failed. Repair the endpoint or verify an official alternative; never disable certificate checks.',
    'transient_network': 'A bounded network attempt failed. Retry normally later; an outage does not mean the clinic closed.',
    'transient_http': 'The server was temporarily unavailable or rate-limited. Respect its retry window; retain existing evidence.',
    'empty_content': 'No readable source text was found. Check the public URL and page format before relying on this source.',
    'extraction_schema': 'The page no longer matches a supported layout. Review and test an adapter before treating extraction as complete.',
    'extraction_limit': 'The bounded extraction was incomplete. Review its size or layout; prior entries were preserved.',
}


def text(value, limit=1800):
    if not isinstance(value, str): return ''
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value).strip()[:limit]


def url(value):
    return value if isinstance(value, str) and len(value) <= 3000 and public_https_url(value) else ''


def read_json(path, fallback):
    try:
        result = json.loads(path.read_text())
        return result if isinstance(result, type(fallback)) else fallback
    except (OSError, ValueError, TypeError):
        return fallback


def publication_configuration(root):
    try:
        workflow = (root / '.github/workflows/daily-site.yml').read_text()
    except OSError:
        return 'not verified'
    values = re.findall(r"^\s*AUTO_PUBLICATION_ENABLED:\s*['\"]?(true|false)['\"]?\s*$", workflow, re.M)
    if values and all(value == 'false' for value in values): return 'paused'
    if 'true' in values: return 'configured on'
    return 'not verified'


def collect(data, clinics, now=None):
    """Project only public, necessary fields; do not mutate inputs or queues."""
    now = now or dt.datetime.now(dt.timezone.utc)
    by_id = {c['id']: c for c in clinics}
    items = []
    errors = []
    sources = [
        ('review_queue.json', 'source_change'),
        ('discovery_queue.json', 'discovery'),
        ('directory_queue.json', 'discovery'),
        ('registry_audit_queue.json', 'manual_audit'),
    ]
    counts_by_queue = {}
    for filename, group in sources:
        raw = read_json(data / filename, {})
        rows = raw.get('items')
        if not isinstance(rows, list):
            errors.append(filename + ': review queue unavailable or malformed')
            counts_by_queue[filename] = None
            continue
        pending = [r for r in rows if isinstance(r, dict) and r.get('review_status') == 'pending']
        counts_by_queue[filename] = len(pending)
        for index, row in enumerate(pending):
            clinic_ids = row.get('clinic_ids', [])
            if isinstance(clinic_ids, str): clinic_ids = [clinic_ids]
            if not isinstance(clinic_ids, list):
                errors.append(filename + ': a finding has malformed clinic references; inspect its original record')
                clinic_ids = []
            names = [by_id[cid].get('name', cid) for cid in clinic_ids if isinstance(cid, str) and cid in by_id]
            title = text(row.get('title'), 220) or ', '.join(names) or 'Public source change requires review'
            default = ('Compare the original clinic page and specific location. Check ongoing-care intake, eligibility and dated evidence before changing any listing.'
                       if group == 'source_change' else 'Verify identity, office address, duplicates, the 75 km boundary, care model and direct clinic evidence. This is not a confirmed opening.')
            item = {'id': f'{filename}:{text(row.get("id"), 100) or index}', 'group': group,
                    'title': title, 'date': text(row.get('detected_at'), 40),
                    'source_url': url(row.get('url') or row.get('news_link')),
                    'secondary_url': url(row.get('second_url')),
                    'queue_url': REPO_URL + '/blob/main/data/' + filename,
                    'action': text(row.get('proposed_action')) or default,
                    'note': text(row.get('note')) or 'Unverified research only. No clinic status change is authorized by this item.',
                    'prior_excerpt': text(row.get('prior_excerpt')),
                    'current_excerpt': text(row.get('current_excerpt') or row.get('excerpt')),
                    'version': text(row.get('extraction_version'), 80) or 'Legacy observation; compare directly before use',
                    'source_name': text(row.get('source_name') or row.get('source_kind'), 180)}
            # Deliberately omit heuristic possible_claim labels: they are not
            # confirmed facts and may be misleading in old pending queue items.
            items.append(item)

    state = read_json(data / 'source_state.json', {})
    extra = read_json(data / 'discovery_sources.json', [])
    expected = {c.get('evidence_url') for c in clinics if url(c.get('evidence_url'))}
    expected.update(s.get('url') for s in extra if isinstance(s, dict) and url(s.get('url')))
    owner_names = {}
    for c in clinics:
        owner_names.setdefault(c.get('evidence_url'), []).append(c.get('name', c['id']))
    stored = state.get('sources') if isinstance(state.get('sources'), dict) else {}
    for source_url in sorted(expected):
        record = stored.get(source_url, {})
        if not isinstance(record, dict): record = {}
        if not record.get('last_error') and record.get('last_attempt'): continue
        category = text(record.get('error_category'), 70) or ('unscanned' if not record.get('last_attempt') else 'unclassified')
        items.append(failure_item('source:' + source_url, ', '.join(owner_names.get(source_url, [])) or urlsplit(source_url).hostname,
                                  source_url, record, category, 'Clinic/source check'))

    directories = read_json(data / 'curated_directories.json', [])
    directory_state = read_json(data / 'directory_state.json', {})
    stored = directory_state.get('sources') if isinstance(directory_state.get('sources'), dict) else {}
    for source in directories:
        if not isinstance(source, dict): continue
        record = stored.get(source.get('id'), {})
        if not isinstance(record, dict): record = {}
        if not record.get('last_error') and record.get('last_attempt'): continue
        category = text(record.get('error_category'), 70) or ('unscanned' if not record.get('last_attempt') else 'unclassified')
        items.append(failure_item('directory:' + str(source.get('id')), source.get('name'), source.get('url'), record, category, 'Directory check'))

    registry = read_json(data / 'official_registry_state.json', {})
    seen = registry.get('seen') if isinstance(registry.get('seen'), dict) else {}
    for ident, observation in seen.items():
        if not isinstance(observation, dict) or not isinstance(observation.get('row'), dict): continue
        row = observation['row']
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('id', 'name', 'address', 'community')):
            errors.append('A malformed government profile observation was withheld')
            continue
        if existing_clinic(row, clinics): continue
        normalize=lambda value:re.sub(r'[^a-z0-9]','',str(value or '').casefold())
        overlaps=[c.get('name',c['id']) for c in clinics
                  if office_address(c.get('address'))==office_address(row['address'])
                  and normalize(c.get('community'))==normalize(row['community'])]
        days = observation.get('days')
        day = text(days[-1], 40) if isinstance(days, list) and days else ''
        items.append({'id': 'registry:' + text(ident, 100), 'group': 'registry_profile',
                      'title': text(row['name'], 220), 'date': day,
                      'source_url': REGISTRY_URL, 'queue_url': REPO_URL + '/blob/main/data/official_registry_state.json',
                      'source_name': 'Ontario government program-site observation',
                      'action': 'Check whether this is a distinct ongoing-care office, a duplicate, or an administrative/specialist program. Verify its exact location and 75 km boundary. A government listing does not establish current operation or intake.',
                      'current_excerpt': text(row['address'] + ' · ' + row['community']),
                      'note': 'Unmatched by exact office identity, not a confirmed missing clinic. No profile approval or intake claim is created here.'
                              + (' Same-address listings to compare: ' + text('; '.join(overlaps),500) + '. A shared address alone does not establish the same practice.' if overlaps else ''),
                      'version': 'Profile schema ' + str(observation.get('schema_version', 'legacy'))})
    alternate_checks = []
    def add_alternate(name, original, record, observation):
        if not isinstance(observation, dict) or record.get('last_error') or not record.get('last_success'): return
        if observation.get('method') != 'official_language_edition' or observation.get('original_url') != original: return
        observed = url(observation.get('observed_url'))
        if not observed or not url(original) or observed == original: return
        issue = observation.get('original_endpoint_issue')
        issue = issue if isinstance(issue, dict) else {}
        alternate_checks.append({'title': text(name), 'original_url': original, 'observed_url': observed,
            'checked_at': text(record.get('last_success')), 'language': text(observation.get('language')),
            'original_error': text(issue.get('last_error')) or 'Original endpoint not reverified by this alternate check',
            'original_attempt': text(issue.get('last_attempt')) or 'Not recorded'})
    source_records = state.get('sources') if isinstance(state.get('sources'), dict) else {}
    directory_records = directory_state.get('sources') if isinstance(directory_state.get('sources'), dict) else {}
    for source_url in sorted(expected):
        record = source_records.get(source_url, {})
        if isinstance(record, dict):
            add_alternate(', '.join(owner_names.get(source_url, [])) or urlsplit(source_url).hostname,
                          source_url, record, record.get('review_observation'))
    for source in directories:
        if not isinstance(source, dict): continue
        record = directory_records.get(source.get('id'), {})
        if isinstance(record, dict) and record.get('observed_url') == source.get('url'):
            add_alternate(source.get('name'), source.get('original_url'), record, record)

    # Manual reading is supplemental evidence, never a successful automated check.
    manual = read_json(data / 'manual_source_reviews.json', {'reviews': []})
    reviews = manual.get('reviews', [])
    if isinstance(reviews, list):
        for entry in reviews:
            if not isinstance(entry, dict): continue
            source = url(entry.get('source_url'))
            day = text(entry.get('reviewed_on'), 10)
            try:
                reviewed = dt.date.fromisoformat(day)
            except ValueError:
                continue
            if reviewed > now.date() or entry.get('method') != 'rendered_public_page': continue
            finding = text(entry.get('finding'), 1000)
            if not source or not finding: continue
            for item in items:
                if item['group'] == 'failure' and item.get('source_url') == source:
                    item['manual_review'] = {'reviewed_on': day, 'finding': finding}

    items.sort(key=lambda item: (list(GROUPS).index(item['group']), item.get('date', ''), item['title'].casefold()))
    counts = {group: sum(i['group'] == group for i in items) for group in GROUPS}
    return {'generated_at': now.isoformat(), 'items': items, 'counts': counts, 'alternate_source_checks': alternate_checks,
            'counts_by_queue': counts_by_queue, 'total': len(items), 'input_errors': errors,
            'last_source_scan': state.get('last_run'), 'last_directory_scan': directory_state.get('last_run'),
            'automatic_status_publication': publication_configuration(data.parent), 'read_only': True}


def failure_item(ident, title, source_url, record, category, source_name):
    return {'id': ident, 'group': 'failure', 'title': text(title, 220) or 'Source needs attention',
            'date': text(record.get('last_attempt'), 40), 'source_url': url(source_url),
            'source_name': source_name, 'category': category,
            'action': ERROR_ACTIONS.get(category, 'The latest readable check is missing or failed. Inspect the diagnostic record and original public source. Preserve the existing listing; no closure can be inferred.'),
            'note': 'Monitoring failure, not evidence that intake stopped or the practice closed.',
            'last_success': text(record.get('last_success'), 40)}


def render(report, health=None):
    """No script, form, tracking or remote resource requests. All strings escaped."""
    e = html.escape
    counts = report['counts']
    sections = []
    for group, heading in GROUPS.items():
        cards = []
        for item in report['items']:
            if item['group'] != group: continue
            links = ''.join('<a href="' + e(item[k], quote=True) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>'
                            for k, label in [('source_url','Open public source'),('secondary_url','Second register'),('queue_url','Review record on GitHub')]
                            if url(item.get(k)))
            excerpts = ''.join('<div class="excerpt"><h4>' + label + '</h4><p>' + e(item[k]) + '</p></div>'
                               for k, label in [('prior_excerpt','Earlier observed excerpt'),('current_excerpt','Latest observed excerpt / listing')]
                               if item.get(k))
            meta = ' · '.join(v for v in [item.get('date') or 'Date not recorded', item.get('source_name'), item.get('category')] if v)
            last_good = '<p class="meta">Last readable check: ' + e(item.get('last_success') or 'Not recorded') + '</p>' if group == 'failure' else ''
            manual = item.get('manual_review')
            manual_note = ('<p class="meta"><strong>Separate manual rendered-page review: ' + e(manual['reviewed_on'])
                           + '</strong></p><p>' + e(manual['finding'])
                           + '</p><p class="caution">The automated check is still unresolved. This dated manual review does not repair monitoring or guarantee current availability.</p>') if isinstance(manual, dict) else ''
            version = '<p class="meta">' + e(item.get('version', '')) + '</p>' if item.get('version') else ''
            cards.append('<details class="finding"><summary><span>' + e(item['title']) + '</span><small>' + e(meta) + '</small></summary>'
                         + '<div class="body"><p class="action">' + e(item['action']) + '</p><p class="caution">' + e(item['note']) + '</p>'
                         + excerpts + last_good + manual_note + version + '<div class="links">' + links + '</div></div></details>')
        description = ('<p class="caution">These observations did not match the exact stored office identity. Many may already be listed under a different name. The count is <strong>not a count of new or missing clinics</strong>.</p>' if group == 'registry_profile' else '')
        host_summary = ''
        if group == 'failure':
            hosts = Counter(urlsplit(i['source_url']).hostname for i in report['items'] if i['group'] == 'failure' and i.get('source_url'))
            description = '<p class="caution">Counts are failed or unscanned source/directory checks, <strong>not unique clinics</strong>. Multiple checks may use the same site.</p>'
            host_summary = '<p class="meta">By source host: ' + e('; '.join(f'{host}: {count}' for host,count in hosts.most_common())) + '</p>' if hosts else ''
        sections.append('<section id="' + group + '"><details class="group"' + (' open' if group in ('source_change', 'discovery') else '') + '><summary><h2>' + e(heading) + ' <span class="count">' + str(counts[group]) + '</span></h2>' + description + '</summary>'
                        + host_summary + (''.join(cards) if cards else '<p class="empty">No items in this category in the current snapshot. This does not establish complete coverage.</p>') + '</details></section>')
    stage_cards = []
    if isinstance(health, dict):
        stages = health.get('stages')
        if stages is not None and not isinstance(stages, dict):
            stage_cards.append('<li>Research-stage health is malformed or unavailable; do not infer successful coverage.</li>')
        for name, stage in (stages if isinstance(stages, dict) else {}).items():
            if not isinstance(stage, dict): continue
            status = stage.get('status') or ('healthy' if stage.get('healthy') is True else 'attention needed')
            if status not in {'healthy','degraded','invalid','failed','stale','unavailable','manual_only','manual_state_invalid','attention needed'}:
                status = 'unknown'
            if status == 'healthy' and stage.get('healthy') is not True:
                status = 'invalid'
            problems = stage.get('problems') or []
            if not isinstance(problems, list): problems = [str(problems)]
            stage_cards.append('<li><strong>' + e(str(stage.get('label') or name).replace('_',' ')) + ':</strong> ' + e(str(status).replace('_',' '))
                               + ('. ' + e('; '.join(str(p) for p in problems)) if problems else '') + '</li>')
    alternates = []
    for item in report.get('alternate_source_checks', []):
        alternates.append('<details class="alternate-check"><summary>' + e(item['title']) + '</summary><div class="body">'
            + '<p>Monitoring is available through the publisher’s official French edition. This does not mean the original endpoint was repaired and does not confirm intake.</p>'
            + '<p class="meta">Alternate checked: ' + e(item['checked_at']) + '</p>'
            + '<p class="meta">Original last attempted: ' + e(item['original_attempt']) + ' · ' + e(item['original_error']) + '</p>'
            + '<div class="links"><a href="' + e(item['original_url'], quote=True) + '" target="_blank" rel="noopener noreferrer">Original source</a>'
            + '<a href="' + e(item['observed_url'], quote=True) + '" target="_blank" rel="noopener noreferrer">Official alternate source</a></div></div></details>')
    alternate_section = ('<section id="official-alternates"><details class="group"><summary><h2>Checks using official alternate sources <span class="count">'
                         + str(len(alternates)) + '</span></h2></summary>' + ''.join(alternates) + '</details></section>') if alternates else ''
    errors = ''.join('<li>' + e(err) + '</li>' for err in report.get('input_errors', []))
    nav = ''.join('<a href="#' + key + '">' + e(label) + ' (' + str(counts[key]) + ')</a>' for key,label in GROUPS.items())
    publication = report.get('automatic_status_publication', 'not verified')
    publication_notice = 'Automatic status publication is paused.' if publication == 'paused' else 'Automatic status publication configuration: ' + e(str(publication)) + '.'
    return ('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; object-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'">
<meta name="referrer" content="no-referrer"><title>Review findings | Primary Care Availability</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f5f8f7;color:#243c4a;font:16px/1.55 system-ui,sans-serif}header{background:#15394a;color:white;padding:28px max(20px,calc((100% - 1100px)/2))}h1{line-height:1.15;margin:8px 0 14px;font-size:clamp(28px,4vw,40px)}header p{color:#d6e6e8;max-width:850px}header a{color:#fff}.wrap{max-width:1140px;margin:auto;padding:24px 20px 70px}.notice{padding:16px 18px;background:#fff7e7;border:1px solid #dfca9a;border-radius:10px;color:#67491a}.links,nav{display:flex;flex-wrap:wrap;gap:12px}a{color:#145b70;text-underline-offset:3px;overflow-wrap:anywhere}nav{margin:22px 0}nav a{background:white;padding:8px 12px;border:1px solid #c8d8db;border-radius:8px;text-decoration:none;font-size:14px}section{margin:30px 0;scroll-margin-top:15px}h2{font-size:23px;color:#173548}.count{font-size:14px;background:#e4edee;padding:4px 9px;border-radius:20px;vertical-align:middle}.finding,.alternate-check{border:1px solid #cfdddf;border-radius:10px;margin:10px 0;background:white;overflow:hidden}.finding summary,.alternate-check summary{cursor:pointer;padding:16px 18px;font-weight:650;overflow-wrap:anywhere}.finding summary small{display:block;font-size:12px;font-weight:400;color:#60727a;margin-top:4px}.body{padding:0 18px 20px}.action{font-weight:600}.caution,.meta,.empty{font-size:13px;color:#5f727c}.excerpt{border-left:3px solid #c5d7db;padding:0 12px;background:#f7fafb;overflow-wrap:anywhere}.excerpt h4{padding-top:8px;font-size:13px;margin-bottom:4px}.excerpt p{font-size:13px;white-space:pre-wrap;padding-bottom:8px}details.instructions{background:#eaf2f3;padding:15px 18px;border-radius:10px;margin:20px 0}.instructions summary{font-weight:700;cursor:pointer}.links a{font-size:13px;font-weight:650}a:focus-visible,summary:focus-visible{outline:3px solid #b87513;outline-offset:3px}.health{background:white;border:1px solid #cfdddf;padding:14px 20px;border-radius:10px}.health li{margin:8px 0;font-size:14px}@media(max-width:550px){.wrap{padding:18px 14px 50px}.finding summary,.alternate-check summary{padding:14px}.body{padding:0 14px 16px}nav a{flex:1 1 45%;font-size:12px}h2{font-size:20px}.links{flex-direction:column}}</style></head><body><header><a href="index.html">← Back to clinic directory</a><h1>Review findings</h1><p>One place to inspect source changes, possible new offices and monitoring gaps. These are research tasks, not confirmed intake changes.</p></header><main class="wrap">'''
    + '<div class="notice"><strong>Read-only review inbox. ' + publication_notice + '</strong> Every finding is unverified research, not an approved opening or closure. Nothing on this page changes a listing. Confirm current, location-specific clinic evidence before publishing. Missing pages never establish closure. Public clinic information only; do not add patient details.</div>'
    + '<p class="meta">Snapshot generated ' + e(report['generated_at']) + '. Latest clinic-source scan: ' + e(str(report.get('last_source_scan') or 'Not recorded')) + '. Latest directory scan: ' + e(str(report.get('last_directory_scan') or 'Not recorded')) + '. New findings appear after a successful research run and site rebuild, not instantly.</p>'
    + '<nav aria-label="Review categories">' + nav + '</nav>'
    + '<details class="instructions"><summary>How to finish a review</summary><ol><li>Open the original public source and verify the exact office, service type, eligibility and current evidence. Headlines and registers do not prove intake.</li><li>For an existing listing, return to the directory’s <strong>Edit listing</strong> tool. Review the proposed edit and publish only through the authenticated GitHub confirmation workflow. For a possible new office, verify identity, duplicates, exact coordinates and the 75 km boundary before creating a reviewed profile with intake unconfirmed.</li><li>Record the review outcome in the linked GitHub queue. This page has no approve/reject or save action and does not resolve queue items automatically.</li></ol><a href="' + REPO_URL + '/issues" target="_blank" rel="noopener noreferrer">Open research and monitoring issues on GitHub</a></details>'
    + ('<section class="health"><h2>Research-stage health</h2><ul>' + ''.join(stage_cards) + '</ul><p class="meta">A green build is not proof of source coverage or clinic availability.</p></section>' if stage_cards else '')
    + ('<div class="notice"><strong>Some review inputs could not be loaded.</strong><ul>' + errors + '</ul></div>' if errors else '')
    + alternate_section + ''.join(sections) + '<p class="meta">Static public-source review only. Not a complete provider census, live roster check, or PHIPA-certified patient-record system.</p></main></body></html>')


def write_dashboard(root, clinics, health=None):
    report = collect(root / 'data', clinics)
    (root / 'site' / 'review.html').write_text(render(report, health), encoding='utf8')
    return report
