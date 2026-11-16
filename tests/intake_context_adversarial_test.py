#!/usr/bin/env python3
"""Independent adversarial intake pipeline tests; synthetic public text, no network/writes.

Exercise fake HTTP -> source extraction -> observation -> publication -> validation.
The observation wiring deliberately mirrors check_sources.run; no handcrafted
positive decision bypasses source parsing. Negative cases are safety requirements,
not a claim the narrow deterministic parser understands arbitrary natural language.
"""
from __future__ import annotations
import contextlib
import copy
import datetime as dt
import io
import inspect
import json
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import requests
import common
import check_sources as scanner
import auto_evidence as evidence
import auto_publish as publisher

URL = 'https://exampleclinic.ca/patients'
POSITIVE = 'Our family practice is now accepting new patients.'
NEGATIVE = 'Our family practice is not accepting new patients.'
CLOSURE = 'Our clinic is permanently closed.'
DAYS = ('2026-11-15T13:00:00+00:00', '2026-11-16T13:00:00+00:00')


def clinic():
    record = {'id': 'c900', 'name': 'Example Clinic', 'community': 'Tillsonburg',
            'address': '1 Main Street', 'clinic_type': 'MD', 'status': 'unknown',
            'clinic_url': 'https://exampleclinic.ca/', 'evidence_url': URL,
            'last_reviewed': '2026-11-09', 'care_model': 'ongoing',
            'clinic_address_verified': True, 'address_verification_source': URL,
            'latitude': 42.8654, 'longitude': -80.7228,
            'coordinate_source': URL,
            'coordinate_precision': 'clinic_address',
            'coordinate_verification_source': URL,
            'auto_publication_scope': {
                'version': 1, 'clinic_id': 'c900', 'source_url': URL,
                'scope': 'single_office', 'reviewed_on': '2026-11-14',
                'method': 'independent_public_source_review',
                'evidence': 'Example Clinic, 1 Main Street, Tillsonburg; this page describes this single office.'}}
    record['auto_publication_scope']['identity_hash'] = evidence.scope_identity(record)
    # Approve ONLY the known canonical synthetic office page. Never derive an
    # approval from the arbitrary/adversarial page supplied to pipeline().
    canonical = evidence.publication_candidate(page(f'<p>{POSITIVE}</p>'))
    record['auto_publication_scope']['context_template_hash'] = canonical['template_hash']
    return record


def database(record=None):
    return {'clinics': [copy.deepcopy(record or clinic())], 'data_as_of': '2026-11-09',
            'center': {'latitude': 42.8654, 'longitude': -80.7228, 'radius_km': 75}}


def page(content, heading='Example Clinic', title='Example Clinic patient information'):
    return f'<html><head><title>{title}</title></head><body><main><h1>{heading}</h1>{content}</main></body></html>'


class Response:
    def __init__(self, html, status=200, url=URL, content_type='text/html'):
        self.status_code = status
        self.url = url
        self.headers = {'Content-Type': content_type}
        self.text = html
        self.content = html.encode()
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)


def fetched(html, final_url=URL, status=200):
    with patch.object(scanner.requests, 'get', return_value=Response(html, status, final_url)), patch.object(scanner.time, 'sleep'):
        returned_url, result = scanner.fetch_one((URL, {'clinics': ['c900'], 'kind': 'intake evidence'}))
    assert returned_url == URL
    return result


def scan_record(result, prev, now, record=None):
    record = record or clinic()
    if result.get('error'):
        return {**prev, 'last_attempt': now, 'last_error': result['error'], 'auto_observation': {}}
    kwargs = {'today': now[:10]} if 'today' in inspect.signature(evidence.first_party).parameters else {}
    verified = evidence.first_party(record, URL, [record['id']], result.get('final_url', URL), **kwargs)
    prior = prev.get('auto_observation', {}) if verified else {}
    candidate = result.get('explicit_candidate') if verified else None
    observation = evidence.observe(prior, candidate, now, scope_hash=evidence.scope_fingerprint(record) if verified else None)
    return {**prev, **result, 'official_first_party': bool(verified), 'last_error': None,
            'last_attempt': now, 'last_success': now,
            'auto_observation': observation}


def pipeline(html, times=DAYS, final_url=URL, status=200, record=None):
    record = record or clinic()
    rec = {}
    for now in times:
        result = fetched(html, final_url, status)
        rec = scan_record(result, rec, now, record)
    db = database(record)
    history = []
    changes, refreshes = publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16')
    return db, history, changes, refreshes, rec


def validate_memory(db):
    """Execute real validator against synthetic in-memory database, never a temp file."""
    output = io.StringIO()
    with patch.object(common, 'load_data', return_value=copy.deepcopy(db)), contextlib.redirect_stdout(output):
        try:
            runpy.run_path(str(ROOT / 'scripts' / 'validate.py'), run_name='__main__')
        except SystemExit as exc:
            if exc.code:
                raise AssertionError(output.getvalue()) from exc


class IntakeContextAdversarialTests(unittest.TestCase):
    def assert_held(self, html, **kwargs):
        db, history, changes, refreshes, rec = pipeline(html, **kwargs)
        self.assertEqual(changes, [], f'Unsafe publication from: {html!r}; candidate={rec.get("auto_observation")}')
        self.assertEqual(refreshes, 0)
        self.assertEqual(history, [])
        self.assertEqual(db, database(kwargs.get('record')))
        validate_memory(db)

    def test_adversarial_context_is_not_published(self):
        cases = {
            'restriction_next_paragraph': page(f'<p>{POSITIVE}</p><p>Residents of our catchment only.</p>'),
            'selected_physicians_next_paragraph': page(f'<p>{POSITIVE}</p><p>This applies only to selected physicians.</p>'),
            'future_next_paragraph': page(f'<p>{POSITIVE}</p><p>This change takes effect in January 2027.</p>'),
            'future_heading': page(f'<p>{POSITIVE}</p>', heading='Opening January 2027'),
            'archive_title': page(f'<p>{POSITIVE}</p>', title='Archived 2020 intake announcement'),
            'historical_heading': page(f'<h2>Archived announcement from 2020</h2><p>{POSITIVE}</p>'),
            'hypothetical': page(f'<p>If funding is approved, we will post the following notice:</p><p>{POSITIVE}</p>'),
            'faq_quoted_example': page(f'<h2>How to read an intake notice</h2><blockquote>{POSITIVE}</blockquote>'),
            'explicit_quoted_other_office': page(f'<p>The following statement comes from another office:</p><blockquote>{POSITIVE}</blockquote>'),
            'cross_office_heading': page(f'<h2>Our London location</h2><p>{POSITIVE}</p><h2>Our Tillsonburg location</h2><p>No current announcement.</p>'),
            'heading_negation': page(f'<h2>Not currently</h2><p>Accepting new patients for ongoing family care.</p>'),
            'paragraph_negates_claim': page(f'<p>{POSITIVE}</p><p>The statement above is no longer correct.</p>'),
            'restriction_after_400_chars': page('<p>' + POSITIVE + ' ' + 'Please read this public notice carefully ' * 15 + ' but eligibility is limited to local residents only.</p>'),
            'restriction_after_9000_chars': page('<p>' + POSITIVE + '</p><p>' + 'Public clinic information. ' * 400 + '</p><p>Registration is limited to residents only.</p>'),
            'temporary_closure': page('<p>Our clinic is temporarily closed.</p>'),
            'closure_with_relocation': page(f'<p>{CLOSURE}</p><p>We have relocated to 10 Main Street and continue to provide family care.</p>'),
            'closure_other_office': page('<h2>Our London location</h2><p>Our clinic is permanently closed.</p><h2>Tillsonburg clinic</h2><p>We continue to provide care here.</p>'),
            'closure_future': page(f'<p>{CLOSURE}</p><p>Effective January 2027.</p>'),
            'hidden_only_claim': page(f'<div hidden>{POSITIVE}</div><p>Contact us for current information.</p>'),
            'aria_hidden_only_claim': page(f'<div aria-hidden="true">{POSITIVE}</div><p>Contact us for current information.</p>'),
            'style_hidden_only_claim': page(f'<p style="display:none">{POSITIVE}</p><p>Contact us for current information.</p>'),
            'generic_new_patients': page('<p>We are now accepting new patients.</p>'),
            'walkin_only': page('<p>We are accepting new patients for walk-in visits and urgent family care.</p>'),
            'contradiction_separate_blocks': page(f'<p>{POSITIVE}</p><p>{NEGATIVE}</p>'),
            'application_button_only': page('<p>Family practice</p><a href="/register">Register now</a>'),
        }
        for name, html in cases.items():
            with self.subTest(name=name):
                self.assert_held(html)

    def test_real_positive_and_negative_controls(self):
        for sentence, expected in [(POSITIVE, 'accepting'), (NEGATIVE, 'not_accepting'), (CLOSURE, 'closed')]:
            with self.subTest(expected=expected):
                db, history, changes, _, rec = pipeline(page(f'<p>{sentence}</p>'))
                self.assertEqual(len(changes), 1, f'Positive control overblocked: {rec}')
                self.assertEqual(len(history), 1)
                if expected == 'closed':
                    self.assertEqual(db['clinics'][0]['operating_status'], 'closed')
                    self.assertEqual(db['clinics'][0]['status'], 'unknown')
                else:
                    self.assertEqual(db['clinics'][0]['status'], expected)
                    self.assertFalse(db['clinics'][0]['intake_verification']['telephone_confirmed'])
                    self.assertFalse(db['clinics'][0]['intake_verification']['enrolment_guaranteed'])
                validate_memory(db)

    def test_second_review_distinct_semantic_and_visibility_traps(self):
        cases = {
            'age_condition_without_only': page(f'<p>{POSITIVE}</p><p>Patients must be aged 65 and over.</p>'),
            'residence_condition_without_only': page(f'<p>{POSITIVE}</p><p>Applicants must reside in our catchment area.</p>'),
            'expired_notice': page(f'<p>{POSITIVE}</p><p>This announcement has expired.</p>'),
            'suspended_intake': page(f'<p>{POSITIVE}</p><p>Intake is suspended.</p>'),
            'subject_to_approval': page(f'<p>{POSITIVE}</p><p>Admission is subject to physician approval.</p>'),
            'unicode_single_quoted_claim': page(f'<p>‘{POSITIVE}’</p>'),
            'deleted_claim': page(f'<del>{POSITIVE}</del><p>Contact us for current information.</p>'),
            'struck_claim': page(f'<s>{POSITIVE}</s><p>Contact us for current information.</p>'),
            'css_class_hidden_claim': page(f'<style>.old-notice {{display:none}}</style><p class="old-notice">{POSITIVE}</p><p>Contact us for current information.</p>'),
            # aria-hidden affects accessibility, not visual display. A visually
            # present condition must not vanish from the evidence context.
            'aria_hidden_visible_restriction': page(f'<p>{POSITIVE}</p><p aria-hidden="true">Residents only.</p>'),
            'samehost_other_office_redirect': None,
        }
        for name, html in cases.items():
            with self.subTest(name=name):
                if name == 'samehost_other_office_redirect':
                    self.assert_held(page(f'<p>{POSITIVE}</p>'), final_url='https://exampleclinic.ca/london-office')
                else:
                    self.assert_held(html)

    def test_legitimate_claim_after_long_unrelated_intro(self):
        html = page('<p>' + 'Welcome to our clinic website. ' * 20 + '</p>' + f'<p>{POSITIVE}</p>')
        # A materially different surrounding context requires explicit review;
        # this harmless fixture is deliberately approved, unlike attack cases.
        record = clinic()
        candidate = evidence.publication_candidate(html)
        self.assertIsNotNone(candidate)
        record['auto_publication_scope']['context_template_hash'] = candidate['template_hash']
        db, _, changes, _, rec = pipeline(html, record=record)
        self.assertEqual(len(changes), 1, f'Legitimate later claim lost: {rec}')
        self.assertEqual(db['clinics'][0]['status'], 'accepting')
        validate_memory(db)

    def test_unapproved_benign_intro_still_requires_review(self):
        html = page('<p>' + 'Welcome to our clinic website. ' * 20 + '</p>' + f'<p>{POSITIVE}</p>')
        self.assert_held(html)

    def test_unrecognized_context_drift_blocked_by_reviewed_template(self):
        # These are deliberately outside the exclusion-word examples. Even
        # when the narrow recognizer extracts an assertion, unknown context
        # cannot autoqualify by remaining unchanged across two daily checks.
        for prose in ('Please bring your purple card.', 'Patients aged twenty can enrol.',
                      'Registration has reached capacity.', 'Adults are served.'):
            with self.subTest(prose=prose):
                html = page(f'<p>{POSITIVE}</p><p>{prose}</p>')
                self.assert_held(html)

    def test_claim_sentence_must_match_whole_statement(self):
        for sentence in ('A brochure says ' + POSITIVE,
                         POSITIVE[:-1] + ', following assessment.',
                         POSITIVE[:-1] + ' when staffing permits.'):
            with self.subTest(sentence=sentence):
                context = evidence.publication_text(page(f'<p>{sentence}</p>'))
                self.assertIsNone(evidence.decisive_statement(context))
                self.assert_held(page(f'<p>{sentence}</p>'))

    def test_new_context_review_cannot_reuse_old_days(self):
        html = page(f'<p>{POSITIVE}</p><p>Please bring your purple card.</p>')
        good = fetched(html)
        self.assertIsNotNone(good['explicit_candidate'])
        original = clinic()
        prior = scan_record(good, {}, '2026-11-14T13:00:00+00:00', original)
        prior = scan_record(good, prior, DAYS[0], original)
        record = clinic()
        record['auto_publication_scope']['context_template_hash'] = good['explicit_candidate']['template_hash']
        record['auto_publication_scope']['reviewed_on'] = '2026-11-16'
        rec = scan_record(good, prior, DAYS[1], record)
        db = database(record); history = []
        self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
        self.assertEqual(db, database(record))
        rec = scan_record(good, rec, '2026-11-17T13:00:00+00:00', record)
        changes, refreshes = publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-17')
        self.assertEqual(len(changes), 1)
        self.assertEqual(refreshes, 0)
        self.assertEqual(history[0]['days_confirmed'], ['2026-11-16', '2026-11-17'])
        validate_memory(db)

    def test_rendering_dependent_sources_cannot_reuse_static_template(self):
        # Each retains the canonical visible claim text. Thus template hashes
        # alone cannot detect rendering/asset changes; the static adapter must
        # reject unsupported markup before it creates a candidate.
        canonical = page(f'<p>{POSITIVE}</p>')
        cases = {
            'external_stylesheet': canonical.replace('</head>', '<link rel="stylesheet" href="/clinic.css"></head>'),
            'mixedcase_stylesheet': canonical.replace('</head>', '<link rel="StyleSheet" href="/clinic.css"></head>'),
            'external_script': canonical.replace('</body>', '<script src="/clinic.js"></script></body>'),
            'inline_script': canonical.replace('</body>', '<script>document.querySelector("p").hidden = true;</script></body>'),
            'inline_event_handler': canonical.replace('<body>', '<body onload="document.querySelector(\'p\').hidden=true">'),
            'inline_style': page(f'<p style="color:green">{POSITIVE}</p>'),
            'collapsed_details': page(f'<details><summary>Patient information</summary><p>{POSITIVE}</p></details>'),
            'closed_dialog': page(f'<dialog><p>{POSITIVE}</p></dialog>'),
            'image_notice': canonical.replace('</main>', '<img src="/intake-restrictions.png" alt="Applicants need an employer referral"></main>'),
            'embedded_notice': canonical.replace('</main>', '<iframe src="/eligibility"></iframe></main>'),
            'svg_notice': canonical.replace('</main>', '<svg><text>Residents only</text></svg></main>'),
        }
        for name, html in cases.items():
            with self.subTest(name=name):
                self.assertIsNone(evidence.publication_text(html))
                self.assert_held(html)

    def test_hidden_conflict_cannot_override_visible_current_claim(self):
        html = page(f'<p>{POSITIVE}</p><p hidden>{NEGATIVE}</p>')
        # This known, benign hidden-text fixture gets an explicit structural
        # review. A structural addition cannot inherit the bare-page approval.
        self.assert_held(html)
        record = clinic()
        candidate = evidence.publication_candidate(html)
        self.assertIsNotNone(candidate)
        record['auto_publication_scope']['context_template_hash'] = candidate['template_hash']
        db, _, changes, _, rec = pipeline(html, record=record)
        self.assertEqual(len(changes), 1, f'Hidden-only conflict overblocked visible public text: {rec}')
        self.assertEqual(db['clinics'][0]['status'], 'accepting')
        validate_memory(db)

    def test_cross_host_and_http_downgrade_redirects(self):
        for url in ('https://another-clinic.ca/patients', 'http://exampleclinic.ca/patients'):
            with self.subTest(url=url):
                self.assert_held(page(f'<p>{POSITIVE}</p>'), final_url=url)

    def test_single_office_scope_requires_explicit_valid_approval(self):
        invalid = [None, {}, {'version': 999}, {'clinic_id': 'c901'},
                   {'source_url': 'https://exampleclinic.ca/other-office'},
                   {'scope': 'program_wide'}, {'reviewed_on': '2027-01-01'},
                   {'reviewed_on': 'not-a-date'}, {'method': 'automated_guess'},
                   {'evidence': ''}]
        for change in invalid:
            with self.subTest(change=change):
                record = clinic()
                if change is None:
                    record.pop('auto_publication_scope')
                elif change == {}:
                    record['auto_publication_scope'] = {}
                else:
                    record['auto_publication_scope'].update(change)
                self.assert_held(page(f'<p>{POSITIVE}</p>'), record=record)

    def test_changed_clinic_identity_invalidates_old_scope(self):
        fields = {'name': 'Different Clinic', 'address': '22 Main Street',
                  'community': 'London', 'clinic_url': 'https://exampleclinic.ca/new-office',
                  'care_model': 'both', 'clinic_type': 'NP'}
        for field, value in fields.items():
            with self.subTest(field=field):
                record = clinic(); record[field] = value
                self.assert_held(page(f'<p>{POSITIVE}</p>'), record=record)

    def test_changed_scope_requires_two_fresh_days_even_when_identity_still_matches(self):
        good = fetched(page(f'<p>{POSITIVE}</p>'))
        original = clinic()
        prior = scan_record(good, {}, DAYS[0], original)
        for change in ({'reviewed_on': '2026-11-15'}, {'evidence': 'Re-reviewed exact office source identity.'}):
            with self.subTest(change=change):
                record = clinic(); record['auto_publication_scope'].update(change)
                rec = scan_record(good, prior, DAYS[1], record)
                db = database(record); history = []
                self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
                self.assertEqual(db, database(record))
                self.assertEqual(history, [])

    def test_rereviewed_changed_identity_cannot_reuse_confirmed_old_observation(self):
        _, _, _, _, rec = pipeline(page(f'<p>{POSITIVE}</p>'))
        record = clinic(); record['address'] = '22 Main Street'
        record['auto_publication_scope']['identity_hash'] = evidence.scope_identity(record)
        db = database(record); history = []
        self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
        self.assertEqual(db, database(record))
        self.assertEqual(history, [])

    def test_failed_or_challenge_fetch_never_builds_observations(self):
        for status, html in [(403, page(f'<p>{POSITIVE}</p>')), (200, '<title>Just a moment...</title><p>Verify you are human</p>'), (200, '<div id="root"></div><script src="app.js"></script>')]:
            with self.subTest(status=status, html=html):
                self.assert_held(html, status=status)

    def test_two_distinct_fresh_days_required(self):
        html = page(f'<p>{POSITIVE}</p>')
        for times in [(DAYS[1],), (DAYS[1], DAYS[1]), ('2026-11-10T13:00:00+00:00', DAYS[1]), ('2026-11-17T13:00:00+00:00', '2026-11-18T13:00:00+00:00'), (DAYS[1], DAYS[0])]:
            with self.subTest(times=times):
                self.assert_held(html, times=times)

    def test_fail_between_successes_breaks_confirmation_chain(self):
        good = fetched(page(f'<p>{POSITIVE}</p>'))
        rec = scan_record(good, {}, DAYS[0])
        rec = scan_record({'error': 'timeout'}, rec, '2026-11-16T09:00:00+00:00')
        rec = scan_record(good, rec, DAYS[1])
        db = database(); history = []
        self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
        self.assertEqual(db, database())
        self.assertEqual(history, [])

    def test_changed_context_requires_two_new_observations(self):
        first = fetched(page(f'<p>{POSITIVE}</p><p>Public information A.</p>'))
        later = fetched(page(f'<p>{POSITIVE}</p><p>Public information B.</p>'))
        rec = scan_record(first, {}, DAYS[0])
        rec = scan_record(later, rec, DAYS[1])
        db = database(); history = []
        self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
        self.assertEqual(db, database())
        self.assertEqual(history, [])

    def test_observation_cannot_outlive_or_contradict_latest_fetch(self):
        _, _, _, _, base = pipeline(page(f'<p>{POSITIVE}</p>'))
        updates = [{'last_success': DAYS[0]}, {'last_success': 'not-a-date'},
                   {'last_error': 'latest fetch failed'}, {'final_url': 'https://another-clinic.ca/'},
                   {'final_url': 'http://exampleclinic.ca/patients'}]
        for update in updates:
            with self.subTest(update=update):
                rec = {**copy.deepcopy(base), **update}
                db = database(); history = []
                self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
                self.assertEqual(db, database())
                self.assertEqual(history, [])

    def test_old_unversioned_observation_must_not_count_as_first_day(self):
        good = fetched(page(f'<p>{POSITIVE}</p>'))
        fresh = scan_record(good, {}, DAYS[0])
        legacy = {k: copy.deepcopy(v) for k, v in fresh['auto_observation'].items() if k in ('status', 'quote', 'first_seen', 'last_seen', 'days')}
        rec = scan_record(good, {'auto_observation': legacy}, DAYS[1])
        db = database(); history = []
        self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
        self.assertEqual(db, database())
        self.assertEqual(history, [])

    def test_unknown_parser_version_never_publishes(self):
        _, _, _, _, rec = pipeline(page(f'<p>{POSITIVE}</p>'))
        obs = copy.deepcopy(rec['auto_observation'])
        keys = [k for k in obs if 'version' in k]
        self.assertTrue(keys, 'Observations must identify the evidence parser version')
        for key in keys:
            obs[key] = 'untrusted-obsolete-parser-version'
        rec['auto_observation'] = obs
        db = database(); history = []
        self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
        self.assertEqual(db, database())
        self.assertEqual(history, [])

    def test_invalid_or_duplicate_observation_days_never_publish(self):
        _, _, _, _, base = pipeline(page(f'<p>{POSITIVE}</p>'))
        for days in (['2026-11-16', '2026-11-16'], ['2026-11-17', '2026-11-18'], ['2026-11-16', '2026-11-15'], ['bad-date', '2026-11-16'], ['2026-10-01', '2026-11-16']):
            with self.subTest(days=days):
                rec = copy.deepcopy(base); rec['auto_observation']['days'] = days
                db = database(); history = []
                self.assertEqual(publisher.apply(db, {'sources': {URL: rec}}, history, '2026-11-16'), ([], 0))
                self.assertEqual(db, database())

    def test_pause_is_retained_and_run_is_non_writing_by_default(self):
        with patch.dict('os.environ', {}, clear=True):
            # Guard the entrypoint's own file reads: apply() is intentionally exercised
            # privately above, but scheduled run() must remain paused without opt-in.
            with patch.object(publisher, 'DB') as db_path, patch.object(publisher, 'SRC') as src_path, patch.object(publisher, 'HISTORY') as history_path, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(publisher.run(), 0)
                db_path.read_text.assert_not_called(); db_path.write_text.assert_not_called()
                src_path.read_text.assert_not_called(); history_path.read_text.assert_not_called()
        workflow = (ROOT / '.github' / 'workflows' / 'daily-site.yml').read_text()
        self.assertIn("AUTO_PUBLICATION_ENABLED: 'false'", workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
