"""Tests for skills/resume-assessment/tools/analyze.py.

The module lives under a path (leading dot, hyphens) that isn't importable
as a normal package, so it's loaded by file path instead.
"""

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest

import yaml

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYZE_PATH = os.path.join(
    PLUGIN_ROOT, "skills", "resume-assessment", "tools", "analyze.py"
)


def _load_analyze():
    spec = importlib.util.spec_from_file_location("analyze", ANALYZE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyze = _load_analyze()


class MeasureTests(unittest.TestCase):
    def test_empty_bullets_no_exception(self):
        # Reproduced crash: a job with bullets: [] used to ZeroDivisionError.
        content = {"experience": [{"role": "Eng", "company": "Acme", "bullets": []}]}
        m = analyze.measure(content)
        self.assertIsNone(m["quantified_pct"])
        self.assertEqual(m["total_bullets"], 0)

    def test_no_experience_key(self):
        m = analyze.measure({})
        self.assertEqual(m["total_bullets"], 0)
        self.assertIsNone(m["quantified_pct"])

    def test_quantified_bullets_counted(self):
        content = {"experience": [{"role": "Eng", "company": "Acme", "bullets": [
            "Improved throughput by 40%",
            "Saved $2M annually",
            "Shipped 12 releases",
        ]}]}
        m = analyze.measure(content)
        self.assertEqual(m["total_bullets"], 3)
        self.assertEqual(m["quantified_total"], 3)
        self.assertEqual(m["unquantified"], [])

    def test_unquantified_bullet_counted(self):
        content = {"experience": [{"role": "Eng", "company": "Acme", "bullets": [
            "Led a team of engineers across two offices",
        ]}]}
        m = analyze.measure(content)
        self.assertEqual(m["quantified_total"], 0)
        self.assertEqual(len(m["unquantified"]), 1)

    def test_long_bullet_boundary(self):
        long_bullet = " ".join(["word"] * 28)
        short_bullet = " ".join(["word"] * 27)
        content = {"experience": [{"role": "Eng", "company": "Acme",
                                    "bullets": [long_bullet, short_bullet]}]}
        m = analyze.measure(content)
        flagged = [text for _, _, text in m["long_bullets"]]
        self.assertIn(long_bullet, flagged)
        self.assertNotIn(short_bullet, flagged)

    def test_outlier_job_flagged(self):
        content = {"experience": [
            {"role": "A", "company": "CoA", "bullets": ["x"] * 6},
            {"role": "B", "company": "CoB", "bullets": ["x"] * 6},
            {"role": "C", "company": "CoC", "bullets": ["x"] * 6},
            {"role": "D", "company": "CoD", "bullets": ["x"] * 2},
        ]}
        m = analyze.measure(content)
        outlier_companies = [company for company, _ in m["outliers"]]
        self.assertIn("CoD", outlier_companies)

    def test_non_outlier_job_not_flagged(self):
        content = {"experience": [
            {"role": "A", "company": "CoA", "bullets": ["x"] * 6},
            {"role": "B", "company": "CoB", "bullets": ["x"] * 6},
            {"role": "C", "company": "CoC", "bullets": ["x"] * 6},
            {"role": "D", "company": "CoD", "bullets": ["x"] * 4},
        ]}
        m = analyze.measure(content)
        outlier_companies = [company for company, _ in m["outliers"]]
        self.assertNotIn("CoD", outlier_companies)


class MainTests(unittest.TestCase):
    def _run_main_with_content(self, content):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.safe_dump(content, f)
            path = f.name
        old_argv = sys.argv
        try:
            sys.argv = ["analyze.py", path]
            with contextlib.redirect_stdout(io.StringIO()) as out:
                analyze.main()
            return out.getvalue()
        finally:
            sys.argv = old_argv
            os.unlink(path)

    def test_no_experience_entries_exits(self):
        with self.assertRaises(SystemExit) as cm:
            self._run_main_with_content({"skills": ["Python"]})
        self.assertEqual(cm.exception.code, "no experience entries found")

    def test_job_with_empty_bullets_does_not_crash(self):
        # This used to raise ZeroDivisionError.
        content = {"experience": [{"role": "Eng", "company": "Acme", "bullets": []}]}
        try:
            output = self._run_main_with_content(content)
        except ZeroDivisionError:
            self.fail("main() raised ZeroDivisionError on a job with no bullets")
        self.assertIn("Quantified: 0/0 (n/a)", output)


if __name__ == "__main__":
    unittest.main()
