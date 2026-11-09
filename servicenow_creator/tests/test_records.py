"""
Tests for the Hebrew and English ServiceNow creator editions.

Compatible with both `python -m unittest discover -s servicenow_creator/tests -v`
(zero extra dependencies) and `pytest servicenow_creator/tests`.
All ServiceNow REST calls are replaced by an in-memory fake, so these tests
never touch a real instance.
"""
import json
import os
import re
import sys
import tempfile
import unittest
from dataclasses import fields
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

_CREATOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _CREATOR_DIR not in sys.path:
    sys.path.insert(0, _CREATOR_DIR)

import servicenow_core as core  # noqa: E402
from create_records import HEBREW_PACK, HEBREW_CHANGE_TEMPLATES  # noqa: E402
from create_records_en import ENGLISH_PACK, ENGLISH_CHANGE_TEMPLATES  # noqa: E402

HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
REQUIRED_TEMPLATE_KEYS = {
    "short_description", "description", "justification", "implementation_plan",
    "risk_impact_analysis", "backout_plan", "test_plan", "change_plan",
    "category", "scope", "priority", "min_duration_hours", "max_duration_hours",
}
FMT = "%Y-%m-%d %H:%M:%S"


def _pack_strings(pack):
    return {f.name: getattr(pack, f.name) for f in fields(pack) if isinstance(getattr(pack, f.name), str)}


def _template_strings(templates):
    for i, tmpl in enumerate(templates):
        for key, value in tmpl.items():
            if isinstance(value, str):
                yield i, key, value


def _window(payload):
    start = datetime.strptime(payload["start_date"], FMT).replace(tzinfo=timezone.utc)
    end = datetime.strptime(payload["end_date"], FMT).replace(tzinfo=timezone.utc)
    return start, end


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeServiceNow:
    """Minimal in-memory stand-in for the ServiceNow Table API."""

    def __init__(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=100)).strftime(FMT)
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(FMT)
        self.active_changes = [
            {"sys_id": "c1", "number": "CHG1", "state": "-2", "start_date": past, "sys_created_on": old},
            {"sys_id": "c2", "number": "CHG2", "state": "-1", "end_date": past, "sys_created_on": old},
            {"sys_id": "c3", "number": "CHG3", "state": "0", "sys_created_on": old},
        ]
        self.active_incidents = [{"sys_id": "i1", "number": "INC1", "sys_created_on": old}]
        self.posts = []
        self.puts = []
        self.counter = 0

    def get(self, url, auth=None, headers=None, params=None):
        table = url.rsplit("/", 1)[-1]
        query = (params or {}).get("sysparm_query", "")
        result = []
        if table == "sys_user_grmember":
            result = [{"group": {"value": "g1"}, "user": {"value": "u1"}}]
        elif table == "change_request" and query == "active=true":
            result = self.active_changes
        elif table == "change_request" and query == "active=true^stateIN-1,0":
            result = [dict(c, short_description=c.get("short_description", "x"), assigned_to="") for c in self.active_changes]
        elif table == "incident":
            result = self.active_incidents
        return FakeResponse(200, {"result": result})

    def post(self, url, auth=None, headers=None, json=None):
        self.counter += 1
        self.posts.append((url.rsplit("/", 1)[-1], json))
        return FakeResponse(201, {"result": {"sys_id": f"new{self.counter}", "number": f"NEW{self.counter}"}})

    def put(self, url, auth=None, headers=None, json=None):
        self.puts.append((url.rsplit("/", 2)[-2], json))
        return FakeResponse(200, {"result": {}})

    def all_text(self):
        bodies = [body for _t, body in self.posts + self.puts]
        return json.dumps(bodies, ensure_ascii=False)


class TestLanguageCatalogs(unittest.TestCase):
    def test_english_templates_contain_no_hebrew(self):
        offenders = [(i, k, v) for i, k, v in _template_strings(ENGLISH_CHANGE_TEMPLATES) if HEBREW_RE.search(v)]
        self.assertEqual(offenders, [])

    def test_english_pack_texts_contain_no_hebrew(self):
        offenders = {k: v for k, v in _pack_strings(ENGLISH_PACK).items() if HEBREW_RE.search(v)}
        self.assertEqual(offenders, {})

    def test_hebrew_templates_text_fields_contain_hebrew(self):
        text_keys = (
            "short_description", "description", "justification",
            "implementation_plan", "risk_impact_analysis",
            "backout_plan", "test_plan", "change_plan",
        )
        for key in text_keys:
            with self.subTest(key=key):
                missing = [i for i, tmpl in enumerate(HEBREW_CHANGE_TEMPLATES) if not HEBREW_RE.search(tmpl[key])]
                self.assertEqual(missing, [])

    def test_hebrew_pack_texts_contain_hebrew(self):
        missing = [k for k, v in _pack_strings(HEBREW_PACK).items() if k != "name" and not HEBREW_RE.search(v)]
        self.assertEqual(missing, [])

    def test_templates_have_all_required_keys(self):
        for label, templates in (("hebrew", HEBREW_CHANGE_TEMPLATES), ("english", ENGLISH_CHANGE_TEMPLATES)):
            with self.subTest(catalog=label):
                for tmpl in templates:
                    self.assertTrue(REQUIRED_TEMPLATE_KEYS <= set(tmpl), tmpl["short_description"])

    def test_english_catalog_mirrors_hebrew_catalog_metadata(self):
        self.assertEqual(len(ENGLISH_CHANGE_TEMPLATES), len(HEBREW_CHANGE_TEMPLATES))
        for he, en in zip(HEBREW_CHANGE_TEMPLATES, ENGLISH_CHANGE_TEMPLATES):
            for key in ("category", "scope", "priority", "min_duration_hours", "max_duration_hours"):
                self.assertEqual(he[key], en[key], (key, en["short_description"]))

    def test_language_pack_texts_are_not_empty(self):
        for pack in (HEBREW_PACK, ENGLISH_PACK):
            with self.subTest(pack=pack.name):
                empty = [k for k, v in _pack_strings(pack).items() if not v.strip()]
                self.assertEqual(empty, [])


class TestPayloadAndScheduleLogic(unittest.TestCase):
    def test_implement_payload_is_running_now(self):
        for pack in (HEBREW_PACK, ENGLISH_PACK):
            for i in range(25):
                with self.subTest(pack=pack.name, iteration=i):
                    now = datetime.now(timezone.utc)
                    start, end = _window(core.generate_change_payload(pack, state_target="implement"))
                    self.assertLessEqual(start, now)
                    self.assertLess(now, end)
                    self.assertGreaterEqual(end - start, timedelta(hours=3))
                    self.assertLessEqual(end - start, timedelta(hours=120))

    def test_pipeline_payload_starts_in_future(self):
        for pack in (HEBREW_PACK, ENGLISH_PACK):
            for i in range(25):
                with self.subTest(pack=pack.name, iteration=i):
                    now = datetime.now(timezone.utc)
                    start, end = _window(core.generate_change_payload(pack, state_target="pipeline"))
                    self.assertGreater(start, now)
                    self.assertGreater(end, start)

    def test_closed_payload_started_days_ago(self):
        for pack in (HEBREW_PACK, ENGLISH_PACK):
            for i in range(25):
                with self.subTest(pack=pack.name, iteration=i):
                    now = datetime.now(timezone.utc)
                    start, _end = _window(core.generate_change_payload(pack, state_target="closed"))
                    self.assertGreaterEqual(start, now - timedelta(days=8))
                    self.assertLessEqual(start, now - timedelta(days=4) + timedelta(minutes=1))

    def test_payload_uses_only_templates_from_its_own_pack(self):
        for pack in (HEBREW_PACK, ENGLISH_PACK):
            short_descriptions = {t["short_description"] for t in pack.change_templates}
            for _ in range(30):
                payload = core.generate_change_payload(pack, ag_id="g1", user_id="u1")
                self.assertIn(payload["short_description"], short_descriptions)
                self.assertEqual(payload["assignment_group"], "g1")
                self.assertEqual(payload["assigned_to"], "u1")
                self.assertEqual(payload["work_notes"], pack.change_work_notes)

    def test_payload_omits_assignee_when_no_user(self):
        payload = core.generate_change_payload(ENGLISH_PACK, ag_id="g1", user_id="")
        self.assertNotIn("assigned_to", payload)

    def test_production_flag_follows_short_description(self):
        prod = next(t for t in ENGLISH_CHANGE_TEMPLATES if "Production" in t["short_description"])
        other = next(t for t in ENGLISH_CHANGE_TEMPLATES if "Production" not in t["short_description"])
        with patch.object(core.random, "choice", side_effect=lambda seq: prod if seq is ENGLISH_CHANGE_TEMPLATES else seq[0]):
            self.assertEqual(core.generate_change_payload(ENGLISH_PACK)["production_system"], "true")
        with patch.object(core.random, "choice", side_effect=lambda seq: other if seq is ENGLISH_CHANGE_TEMPLATES else seq[0]):
            self.assertEqual(core.generate_change_payload(ENGLISH_PACK)["production_system"], "false")

    def test_is_israel_weekend(self):
        cases = [
            ("2026-11-12", 23, False),  # Thursday night
            ("2026-11-13", 12, False),  # Friday 12:00
            ("2026-11-13", 13, True),   # Friday 13:00 -> weekend starts
            ("2026-11-14", 10, True),   # Saturday morning
            ("2026-11-14", 20, True),   # Saturday 20:00
            ("2026-11-14", 21, False),  # Saturday 21:00 -> weekend over
            ("2026-11-15", 9, False),   # Sunday
        ]
        for day, hour, expected in cases:
            with self.subTest(day=day, hour=hour):
                dt = datetime.strptime(f"{day} {hour:02d}:00:00", FMT)
                self.assertIs(core.is_israel_weekend(dt), expected)

    def test_run_skips_everything_on_weekend(self):
        def boom(*_a, **_k):
            raise AssertionError("must not be called on the weekend")

        with patch.object(core, "is_israel_weekend", return_value=True), \
             patch.object(core, "load_config", side_effect=boom), \
             patch.object(core.requests, "get", side_effect=boom):
            core.run(ENGLISH_PACK)

    def test_load_config_normalizes_instance(self):
        for raw in ("dev123", "dev123.service-now.com", "https://dev123.service-now.com/"):
            with self.subTest(raw=raw), patch.dict(os.environ, {
                "SN_INSTANCE": raw, "SN_USERNAME": "user", "SN_PASSWORD": "pass",
            }, clear=False):
                core.load_config()
                self.assertEqual(core.BASE_URL, "https://dev123.service-now.com/api/now/table")
                self.assertEqual(core.AUTH, ("user", "pass"))


class TestEndToEndMockRun(unittest.TestCase):
    def _run_with_fake(self, pack):
        fake = FakeServiceNow()
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = os.path.join(tmpdir, "summary.md")
            env = {
                "SN_INSTANCE": "dev123",
                "SN_USERNAME": "user",
                "SN_PASSWORD": "pass",
                "GITHUB_STEP_SUMMARY": summary_path,
            }
            with patch.dict(os.environ, env, clear=False), \
                 patch.object(core.requests, "get", side_effect=fake.get), \
                 patch.object(core.requests, "post", side_effect=fake.post), \
                 patch.object(core.requests, "put", side_effect=fake.put), \
                 patch.object(core, "_CACHED_GRMEMBERS", []), \
                 patch.object(core, "is_israel_weekend", return_value=False), \
                 patch.object(core.random, "random", return_value=0.0), \
                 patch.object(core.random, "randint", side_effect=lambda a, b: a):
                core.run(pack)
            with open(summary_path, encoding="utf-8") as f:
                summary = f.read()
        return fake, summary

    def test_english_run_writes_no_hebrew_to_servicenow(self):
        fake, summary = self._run_with_fake(ENGLISH_PACK)
        tables = {t for t, _b in fake.posts}
        self.assertTrue({"change_request", "incident", "problem"} <= tables)
        self.assertIsNone(HEBREW_RE.search(fake.all_text()))
        self.assertIn("Assigned to: Infrastructure Team", summary)
        self.assertIsNone(HEBREW_RE.search(summary))

    def test_english_run_writes_english_lifecycle_notes(self):
        fake, _summary = self._run_with_fake(ENGLISH_PACK)
        text = fake.all_text()
        for note in (
            ENGLISH_PACK.implement_start_note, ENGLISH_PACK.implement_done_note,
            ENGLISH_PACK.review_close_notes, ENGLISH_PACK.quota_close_notes,
            ENGLISH_PACK.incident_close_notes, ENGLISH_PACK.incident_short_description,
            ENGLISH_PACK.problem_short_description,
        ):
            self.assertIn(note, text)

    def test_hebrew_run_writes_hebrew_records(self):
        fake, summary = self._run_with_fake(HEBREW_PACK)
        created_changes = [b for t, b in fake.posts if t == "change_request"]
        self.assertTrue(created_changes)
        self.assertTrue(all(HEBREW_RE.search(b["short_description"]) for b in created_changes))
        text = fake.all_text()
        self.assertIn(HEBREW_PACK.implement_start_note, text)
        self.assertIn(HEBREW_PACK.incident_close_notes, text)
        self.assertNotIn(ENGLISH_PACK.implement_start_note, text)
        self.assertIn("מוקצה ל: צוות תשתיות", summary)

    def test_run_enforces_change_quotas(self):
        fake, _summary = self._run_with_fake(ENGLISH_PACK)
        created_changes = [b for t, b in fake.posts if t == "change_request"]
        # 8 in Implement + 8 Closed (fake has none) + pipeline top-up to 16 active (fake reports 3)
        self.assertEqual(len(created_changes), 8 + 8 + (16 - 3))


if __name__ == "__main__":
    unittest.main()
