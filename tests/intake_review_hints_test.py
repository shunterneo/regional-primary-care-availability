"""Review-only regression coverage: clinician negation and specialist queues."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from intake_evidence import classify, REVIEW_CLASSIFIER_VERSION


class IntakeReviewHintsTest(unittest.TestCase):
    def test_forbes_negated_clinician_availability(self):
        for sentence in (
            'We do not have any physicians accepting patients at this time.',
            'We do not have any physicians accepting new patients at this time.',
            "We don't have any doctors currently accepting new patients.",
            'We don’t have any providers accepting patients.',
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(classify(sentence), {
                    'classification': 'possible_closed', 'excerpts': [sentence],
                    'confidence': 'text_match_only',
                })

    def test_positive_and_conflicting_clinician_controls(self):
        positive = 'We have physicians accepting patients at this time.'
        self.assertEqual(classify(positive)['classification'], 'possible_accepting')
        negative = 'We do not have any physicians accepting patients at this time.'
        self.assertEqual(classify(negative + ' ' + positive)['classification'],
                         'conflicting_or_conditional')

    def test_st_andrews_specialist_wait_time_is_not_primary_care_queue(self):
        for sentence in (
            'Typically 1-3 weeks, depending on the specialist’s waitlist.',
            "Typically 1-3 weeks, depending on the specialist's waitlist.",
            'Depending on the specialists’ waiting list.',
            'Depending on the specialist wait list.',
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(classify(sentence), {
                    'classification': 'unclear', 'excerpts': [],
                    'confidence': 'insufficient',
                })

    def test_primary_care_and_unspecified_waitlists_remain_reviewable(self):
        for sentence in (
            'Our waitlist is currently open.',
            'Join the waiting list for a family physician.',
            'We maintain an attachment queue.',
            'Our family practice waitlist is separate from the specialist’s waitlist.',
            'The specialist can refer patients to our family practice waiting list.',
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(classify(sentence)['classification'], 'possible_waitlist')

    def test_specialist_queue_does_not_hide_other_hints(self):
        sentence = 'We are accepting new patients, regardless of the specialist’s waitlist.'
        self.assertEqual(classify(sentence)['classification'], 'possible_accepting')

    def test_review_version_changed_without_enabling_writer(self):
        self.assertEqual(REVIEW_CLASSIFIER_VERSION, 'intake-hints-v3')
        workflow = (ROOT / '.github/workflows/daily-site.yml').read_text()
        self.assertIn("AUTO_PUBLICATION_ENABLED: 'false'", workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
