import json
import pathlib
import subprocess
import sys
import unittest

from coverage_witness import reconcile


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def load_fixture(name):
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return json.load(handle)


class ReconcileTests(unittest.TestCase):
    def test_complete_fixture_is_covered(self):
        result = reconcile(load_fixture("complete.json"))
        self.assertEqual(result["verdict"], "covered")
        self.assertEqual([item["status"] for item in result["coverage"]], ["covered", "covered"])

    def test_omitted_path_is_missing(self):
        result = reconcile(load_fixture("omitted.json"))
        self.assertEqual(result["verdict"], "missing")
        self.assertEqual(result["coverage"][1]["status"], "missing")

    def test_duplicate_reads_are_evidence_but_not_two_paths(self):
        result = reconcile(load_fixture("duplicate-events.json"))
        self.assertEqual(result["verdict"], "covered")
        self.assertEqual(result["coverage"][0]["observed_event_indexes"], [0, 1])

    def test_malformed_event_is_unknown(self):
        result = reconcile(load_fixture("malformed-event.json"))
        self.assertEqual(result["verdict"], "unknown")
        self.assertTrue(any(issue["code"] == "path_not_string" for issue in result["unknown"]))

    def test_path_aliases_are_normalised(self):
        result = reconcile(load_fixture("path-alias.json"))
        self.assertEqual(result["verdict"], "covered")

    def test_claim_cannot_add_coverage(self):
        result = reconcile(load_fixture("unsupported-claim.json"))
        self.assertEqual(result["verdict"], "unknown")
        self.assertTrue(any(issue["code"] == "claim_exceeds_manifest" for issue in result["unknown"]))

    def test_unsafe_paths_are_explicitly_unknown(self):
        result = reconcile({
            "manifest": ["../secret.txt"],
            "events": [],
            "claim": {"status": "complete"},
        })
        self.assertEqual(result["verdict"], "unknown")
        self.assertTrue(any(issue["code"] == "path_escapes_root" for issue in result["unknown"]))

    def test_repeated_runs_are_byte_identical(self):
        document = load_fixture("complete.json")
        outputs = [json.dumps(reconcile(document), sort_keys=True, separators=(",", ":")) for _ in range(3)]
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])

    def test_cli_integration_sample(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "coverage_witness.py"), "--input", str(FIXTURES / "complete.json")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["verdict"], "covered")


if __name__ == "__main__":
    unittest.main()
