import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness import ReliabilityHarness
from support_agent import SupportTriageAgent


class ReliabilityTests(unittest.TestCase):
    def test_dataset_has_at_least_twenty_cases_and_edge_cases(self):
        cases = json.loads((ROOT / "evaluation_cases.json").read_text())
        self.assertGreaterEqual(len(cases), 20)
        groups = {c["group"] for c in cases}
        self.assertTrue({"multi_intent", "negation", "typo", "multilingual", "empty"}.issubset(groups))

    def test_success_requires_all_expected_fields(self):
        cases = [{"id":"T1", "group":"test", "input":"refund", "expected":{
            "category":"billing", "priority":"normal", "action":"wrong_action"}}]
        rows = ReliabilityHarness(SupportTriageAgent()).evaluate(cases, repeats=1)
        self.assertFalse(rows[0]["success"])
        self.assertIn("action", rows[0]["error"])

    def test_repeats_are_counted(self):
        cases = [{"id":"T1", "group":"test", "input":"refund", "expected":{
            "category":"billing", "priority":"normal", "action":"route_billing"}}]
        harness = ReliabilityHarness(SupportTriageAgent())
        rows = harness.evaluate(cases, repeats=3)
        summary = harness.summarize(rows, 1, 3)
        self.assertEqual(summary["total_runs"], 3)
        self.assertEqual(summary["successful_runs"], 3)
        self.assertEqual(summary["consistency_rate_percent"], 100.0)


if __name__ == "__main__":
    unittest.main()

