from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repolens.core.scanner import analyze_repository
from repolens.formatters.text import render_report


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "sample_repo"


class AnalyzeRepositoryTests(unittest.TestCase):
    def test_sample_repo_reports_python_src_layout(self) -> None:
        report = analyze_repository(FIXTURE_ROOT)

        self.assertEqual(report.summary.layout, "src-layout")
        self.assertEqual(report.summary.dominant_language, "Python")
        self.assertGreaterEqual(report.summary.source_files, 2)
        self.assertGreaterEqual(report.summary.test_files, 1)
        self.assertIn("src/app", report.source_directories)
        self.assertIn("tests", report.test_directories)
        self.assertFalse(any(finding.code == "missing-tests" for finding in report.findings))

    def test_missing_readme_and_tests_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "tool.py").write_text("print('hello')\n", encoding="utf-8")

            report = analyze_repository(root)

        codes = {finding.code for finding in report.findings}
        self.assertIn("missing-readme", codes)
        self.assertIn("missing-tests", codes)

    def test_json_render_is_parseable(self) -> None:
        report = analyze_repository(FIXTURE_ROOT)
        payload = render_report(report, output_format="json")
        parsed = json.loads(payload)

        self.assertEqual(parsed["summary"]["layout"], "src-layout")
        self.assertIsInstance(parsed["findings"], list)


if __name__ == "__main__":
    unittest.main()
