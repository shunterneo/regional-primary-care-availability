"""Full-context review observations cannot become automatic clinic facts."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import check_sources as monitor
from source_observation import document_context, REVIEW_VERSION
from intake_evidence import classify

URL = 'https://example.org/intake'

class Response:
    def __init__(self, text, url=URL, content_type='text/html'):
        self.text = text
        self.content = text.encode()
        self.url = url
        self.headers = {'Content-Type': content_type}
    def raise_for_status(self):
        pass

class ContextObservationTests(unittest.TestCase):
    def digest(self, text, **kwargs):
        return document_context(text, URL, **kwargs)['hash']

    def fetch(self, text):
        with patch.object(monitor, 'request_source', return_value=Response(text)):
            return monitor.fetch_one((URL, {}))[1]

    def test_change_after_both_old_preview_limits(self):
        intro = 'Family physician information. ' * 800
        before = f'<p>{intro}</p><p>Only local residents are eligible.</p>'
        after = before.replace('local residents', 'existing patients')
        self.assertEqual(monitor.extract(before), monitor.extract(after))
        self.assertNotEqual(self.fetch(before)['hash'], self.fetch(after)['hash'])

    def test_non_keyword_qualifier_change_is_detected(self):
        before = '<p>We are accepting new patients.</p><p>Only residents in Ward 2 are eligible.</p>'
        after = before.replace('Ward 2', 'Ward 3')
        self.assertEqual(monitor.extract(before), monitor.extract(after))
        self.assertNotEqual(self.fetch(before)['hash'], self.fetch(after)['hash'])

    def test_header_and_footer_closure_banners_are_observed(self):
        for tag in ('header', 'footer', 'nav'):
            before = f'<{tag}>We have moved to 23 Main Street.</{tag}><p>Family physician information.</p>'
            after = before.replace('moved to 23 Main Street', 'permanently closed')
            self.assertNotEqual(self.fetch(before)['hash'], self.fetch(after)['hash'])
            self.assertIn('permanently closed', self.fetch(after)['excerpt'])

    def test_link_and_image_alt_changes_are_observed(self):
        before = '<p>Family physician information.</p><a href="/apply">Registration</a><img alt="Intake paused">'
        self.assertNotEqual(self.digest(before), self.digest(before.replace('/apply', '/waiting-list')))
        self.assertNotEqual(self.digest(before), self.digest(before.replace('paused', 'open')))

    def test_visibility_base_and_media_changes_are_reviewed(self):
        before = '<p>Family practice information.</p><div>We are accepting new patients.</div><div hidden>We are not accepting new patients.</div>'
        after = '<p>Family practice information.</p><div hidden>We are accepting new patients.</div><div>We are not accepting new patients.</div>'
        self.assertNotEqual(self.digest(before), self.digest(after))
        before = '<head><base href="https://example.org/current/"></head><p>Family practice intake.</p><a href="apply">Apply</a>'
        self.assertNotEqual(self.digest(before), self.digest(before.replace('/current/', '/closed/')))
        before = '<p>Family practice information.</p><img src="/open.png" alt="Intake notice">'
        self.assertNotEqual(self.digest(before), self.digest(before.replace('/open.png', '/closed.png')))

    def test_title_dates_and_redirect_are_bound(self):
        before = '<title>Practice notice 2026</title><meta name="date" content="2026-11-15"><p>Family physician information.</p>'
        self.assertNotEqual(self.digest(before), self.digest(before.replace('2026-11-15', '2020-01-01')))
        self.assertNotEqual(self.digest(before), document_context(before, URL + '/archive')['hash'])

    def test_whitespace_and_cpsos_retrieval_clock_only_are_normalized(self):
        before = '<p>Physician register AS OF THE DATE AND TIME NOTED BELOW 12/11/26 03:43:27 AM. Family physician at 123 Main Street.</p>'
        after = before.replace('03:43:27', '03:55:20').replace('Family physician', 'Family\n   physician')
        self.assertEqual(self.digest(before), self.digest(after))
        self.assertNotEqual(self.digest(before), self.digest(before.replace('123 Main', '125 Main')))

    def test_submitted_values_scripts_and_styles_are_not_observations(self):
        before = '<p>Family practice information.</p><form>PRIVATE <input value="patient"></form><script>track("first")</script><style>.x {color:red}</style>'
        after = before.replace('PRIVATE', 'SECRET').replace('patient', 'other').replace('first', 'second').replace('red', 'blue')
        self.assertEqual(self.digest(before), self.digest(after))
        context = document_context(before, URL)
        self.assertNotIn('PRIVATE', context['text'])
        self.assertNotIn('patient', context['text'])

    def test_raw_hidden_text_is_only_a_review_observation(self):
        body = '<p>Family practice information.</p><div hidden>We are accepting new patients.</div><script src="/app.js"></script>'
        result = self.fetch(body)
        self.assertIsNone(result['explicit_candidate'])
        self.assertIn('no intake verification', result['review_observation']['scope'])
        self.assertNotIn('text', result['review_observation'])

    def test_own_clinic_none_negation_is_not_a_positive_review_hint(self):
        negative = 'None of the physicians in our clinic are currently accepting new patients.'
        self.assertEqual(classify(negative)['classification'], 'possible_closed')
        self.assertEqual(classify(negative + ' A care connector will match you with a doctor who is accepting new patients in your area.')['classification'], 'conflicting_or_conditional')
        self.assertEqual(classify('The physicians in our clinic are currently accepting new patients.')['classification'], 'possible_accepting')

    def test_pdf_full_text_remains_review_only(self):
        class Page:
            def __init__(self, text): self.text = text
            def extract_text(self): return self.text
        class Reader:
            is_encrypted = False
        before = 'Family physician information. ' * 800 + 'Limited to Ward 2.'
        response = Response('%PDF-fixture', content_type='application/pdf')
        hashes = []
        for text in (before, before.replace('Ward 2', 'Ward 3')):
            reader = Reader(); reader.pages = [Page(text)]
            with patch.object(monitor, 'request_source', return_value=response), patch.object(monitor, 'PdfReader', return_value=reader):
                result = monitor.fetch_one((URL, {}))[1]
            self.assertIsNone(result['explicit_candidate'])
            hashes.append(result['hash'])
        self.assertNotEqual(*hashes)

    def test_legacy_observations_are_rebaselined_without_false_alert(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        data_bytes = (root / 'data/clinics.json').read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            state = {'version': 1, 'sources': {URL: {'hash': 'legacy-hash', 'last_success': '2026-11-15T00:00:00+00:00', 'excerpt': 'old'}}}
            queue = {'version': 1, 'items': [{'id': 'existing', 'url': URL, 'new_hash': 'older'}]}
            with patch.multiple(monitor, state=state, queue=queue,
                                state_path=pathlib.Path(temp)/'state.json', queue_path=pathlib.Path(temp)/'queue.json',
                                urlmap={URL: {'clinics': [], 'kind': 'clinic discovery'}}):
                with patch.object(monitor, 'request_source', return_value=Response('<p>Family practice information.</p>')):
                    monitor.run()
                    self.assertEqual(state['last_summary']['extraction_version_baselines'], 1)
                    self.assertEqual(len(queue['items']), 1)
                    self.assertEqual(state['sources'][URL]['previous_extraction']['hash'], 'legacy-hash')
                    self.assertEqual(state['sources'][URL]['extraction_version'], REVIEW_VERSION)
                    monitor.run()
                    self.assertEqual(state['last_summary']['extraction_version_baselines'], 0)
                    self.assertEqual(len(queue['items']), 1)
                with patch.object(monitor, 'request_source', return_value=Response('<p>Family practice has permanently closed.</p>')):
                    monitor.run()
                    self.assertEqual(len(queue['items']), 2)
                    self.assertEqual(queue['items'][-1]['review_status'], 'pending')
                    self.assertEqual(queue['items'][-1]['extraction_version'], REVIEW_VERSION)
                    saved_hash = state['sources'][URL]['hash']
                with patch.object(monitor, 'request_source', side_effect=ValueError('unreadable source')):
                    monitor.run()
                    self.assertEqual(state['sources'][URL]['hash'], saved_hash)
                    self.assertEqual(state['sources'][URL]['auto_observation'], {})
                    self.assertEqual(len(queue['items']), 2)
        self.assertEqual((root / 'data/clinics.json').read_bytes(), data_bytes)

    def test_repeated_real_transitions_are_not_suppressed_by_old_queue_items(self):
        with tempfile.TemporaryDirectory() as temp:
            state = {'sources': {}}
            queue = {'items': []}
            with patch.multiple(monitor, state=state, queue=queue,
                                state_path=pathlib.Path(temp)/'state.json', queue_path=pathlib.Path(temp)/'queue.json',
                                urlmap={URL: {'clinics': [], 'kind': 'clinic discovery'}}):
                for body in ('accepting', 'not accepting', 'accepting', 'not accepting'):
                    with patch.object(monitor, 'request_source', return_value=Response(f'<p>Family practice {body} new patients.</p>')):
                        monitor.run()
                    for item in queue['items']:
                        item['review_status'] = 'resolved'
                self.assertEqual(len(queue['items']), 3)
                self.assertEqual(len({item['id'] for item in queue['items']}), 3)
                with patch.object(monitor, 'request_source', return_value=Response('<p>Family practice not accepting new patients.</p>')):
                    monitor.run()
                self.assertEqual(len(queue['items']), 3)

if __name__ == '__main__':
    unittest.main(verbosity=2)
