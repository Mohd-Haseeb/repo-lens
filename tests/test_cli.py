from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from repolens import __version__
from repolens.cli.app import build_parser, main


class CliTests(unittest.TestCase):
    def test_version_flag_prints_package_version(self) -> None:
        parser = build_parser()

        with io.StringIO() as output, redirect_stdout(output):
            with self.assertRaises(SystemExit) as raised:
                parser.parse_args(["--version"])

            self.assertEqual(raised.exception.code, 0)
            self.assertIn(__version__, output.getvalue())

    def test_scan_returns_error_for_missing_path(self) -> None:
        missing_path = Path(tempfile.gettempdir()) / "repo-lens-missing-path"

        with io.StringIO() as errors, redirect_stderr(errors):
            exit_code = main(["scan", str(missing_path)])
            error_output = errors.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("Path does not exist", error_output)


if __name__ == "__main__":
    unittest.main()
