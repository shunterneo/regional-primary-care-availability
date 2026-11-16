"""Recent updates is a native, collapsed disclosure without removing history."""
import pathlib, unittest
from bs4 import BeautifulSoup
ROOT = pathlib.Path(__file__).resolve().parents[1]

class RecentUpdatesTests(unittest.TestCase):
    def test_default_collapsed_native_disclosure(self):
        for path in ('scripts/site_template.html', 'site/index.html'):
            soup = BeautifulSoup((ROOT/path).read_text(), 'html.parser')
            panel = soup.find('details', id='recentUpdates')
            self.assertIsNotNone(panel)
            self.assertNotIn('open', panel.attrs)
            summary = panel.find('summary', recursive=False)
            self.assertEqual(summary.find('h2').get_text(), 'Recent directory updates')
            self.assertIsNone(summary.get('tabindex'))  # Native keyboard activation remains intact.
            self.assertIsNotNone(panel.find(id='changeHistory'))
            self.assertIn('not telephone confirmation or guaranteed enrolment', panel.get_text())
            self.assertEqual(len(soup.select('#changeHistory')), 1)
    def test_visible_focus_and_state_cues(self):
        text = (ROOT/'scripts/site_template.html').read_text()
        self.assertIn('.recentupdates summary:focus-visible', text)
        self.assertIn('.recentupdates[open] .closedhint{display:none}', text)
        self.assertIn('.recentupdates[open] .openhint{display:inline}', text)
        self.assertIn('min-height:44px', text)

if __name__ == '__main__': unittest.main()
