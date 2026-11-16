"""Static release UI checks, no Streamlit app execution required."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ResearchBaselineUIReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "app.py").read_text(encoding="utf-8")

    def test_baseline_states_it_is_destructive(self):
        self.assertIn("research baseline REPLACES ALL", self.source)
        self.assertIn("Smart Memory Review", self.source)

    def test_confirmation_is_required_for_existing_topic(self):
        self.assertIn("if baseline_existing:", self.source)
        self.assertIn("baseline_confirmed = st.checkbox(", self.source)
        self.assertIn("disabled=bool(baseline_existing) and not baseline_confirmed", self.source)

    def test_confirmation_rekeys_when_proposed_fact_changes(self):
        self.assertIn("hashlib.sha256(", self.source)
        self.assertIn("fact.strip()).encode", self.source)

    def test_smart_review_still_defaults_to_keep_both(self):
        self.assertIn('("Keep both", "Supersede old memory")', self.source)
        self.assertIn('new_id = save_reviewed_memory(', self.source)


if __name__ == "__main__":
    unittest.main()
