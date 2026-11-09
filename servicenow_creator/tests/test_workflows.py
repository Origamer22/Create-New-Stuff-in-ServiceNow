"""
Static tests for the two GitHub Actions workflows.

Compatible with both `python -m unittest discover -s servicenow_creator/tests -v`
(zero extra dependencies) and `pytest servicenow_creator/tests`.
If PyYAML is installed, the files are also validated with `yaml.safe_load`.
"""
import os
import re
import unittest

try:
    import yaml  # optional; installed via requirements-dev.txt
except ImportError:  # pragma: no cover
    yaml = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WF_DIR = os.path.join(ROOT, ".github", "workflows")
HEBREW_WF = os.path.join(WF_DIR, "servicenow_creator.yml")
ENGLISH_WF = os.path.join(WF_DIR, "servicenow_creator_en.yml")
EXPECTED_CRONS = ["0 * * * 0-4", "0 0-9 * * 5", "0 18-23 * * 6"]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hebrew_raw = _read(HEBREW_WF)
        cls.english_raw = _read(ENGLISH_WF)

    def test_workflow_files_exist_and_have_valid_yaml_indentation(self):
        for label, raw in (("hebrew", self.hebrew_raw), ("english", self.english_raw)):
            with self.subTest(workflow=label):
                self.assertNotIn("\t", raw, "YAML files must not contain tabs")
                if yaml is not None:
                    parsed = yaml.safe_load(raw)
                    self.assertIsInstance(parsed, dict)
                    self.assertIn("jobs", parsed)

    def test_workflow_names_identify_language(self):
        self.assertRegex(self.hebrew_raw, r"(?m)^name:\s*ServiceNow Creator \(Hebrew\)\s*$")
        self.assertRegex(self.english_raw, r"(?m)^name:\s*ServiceNow Creator \(English\)\s*$")

    def test_workflows_share_schedule_and_manual_trigger(self):
        for label, raw in (("hebrew", self.hebrew_raw), ("english", self.english_raw)):
            with self.subTest(workflow=label):
                crons = re.findall(r"-\s*cron:\s*'([^']+)'", raw)
                self.assertEqual(crons, EXPECTED_CRONS)
                self.assertRegex(raw, r"(?m)^\s*workflow_dispatch:")

    def test_workflows_share_concurrency_group(self):
        for label, raw in (("hebrew", self.hebrew_raw), ("english", self.english_raw)):
            with self.subTest(workflow=label):
                self.assertRegex(raw, r"(?m)^concurrency:\s*\n\s+group:\s*servicenow-creator\s*\n\s+cancel-in-progress:\s*false\s*$")

    def test_workflows_run_their_own_scripts_with_utf8_and_secrets(self):
        cases = (
            ("hebrew", self.hebrew_raw, "python servicenow_creator/create_records.py"),
            ("english", self.english_raw, "python servicenow_creator/create_records_en.py"),
        )
        for label, raw, cmd in cases:
            with self.subTest(workflow=label):
                self.assertIn(cmd, raw)
                self.assertIn('PYTHONUTF8: "1"', raw)
                self.assertIn("PYTHONIOENCODING: utf-8", raw)
                for secret in ("SN_INSTANCE", "SN_USERNAME", "SN_PASSWORD"):
                    self.assertIn("${{ secrets.%s }}" % secret, raw)

    def test_no_undefined_vars_context_access(self):
        """Ensure neither workflow references `vars.*`, avoiding VS Code GitHub Actions warnings."""
        for label, raw in (("hebrew", self.hebrew_raw), ("english", self.english_raw)):
            with self.subTest(workflow=label):
                self.assertIsNone(re.search(r"\bvars\.", raw))

    def test_keepalive_fetches_latest_remote_tip_before_checking_age(self):
        for label, raw in (("hebrew", self.hebrew_raw), ("english", self.english_raw)):
            with self.subTest(workflow=label):
                self.assertIn("git fetch origin ${{ github.ref_name }}", raw)
                self.assertIn("LAST_COMMIT=$(git log -1 --format=%ct FETCH_HEAD)", raw)


if __name__ == "__main__":
    unittest.main()
