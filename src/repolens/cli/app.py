from __future__ import annotations

import argparse
from pathlib import Path

from repolens.core.scanner import analyze_repository
from repolens.formatters.text import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-lens",
        description="Inspect a repository and surface a few architectural signals.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser(
        "scan",
        help="Analyze a repository and print a summary.",
    )
    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository path to inspect. Defaults to the current directory.",
    )
    scan_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        report = analyze_repository(Path(args.path))
        print(render_report(report, output_format=args.format))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2
