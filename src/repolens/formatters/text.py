from __future__ import annotations

import json

from repolens.core.models import ScanReport


def render_report(report: ScanReport, output_format: str = "text") -> str:
    if output_format == "json":
        return json.dumps(report.to_dict(), indent=2)
    if output_format != "text":
        raise ValueError(f"Unsupported output format: {output_format}")
    return _render_text(report)


def _render_text(report: ScanReport) -> str:
    summary = report.summary

    lines = [
        f"Repo Lens: {summary.root_path}",
        "",
        "Summary",
        f"  layout: {summary.layout}",
        f"  dominant language: {summary.dominant_language}",
        f"  files: {summary.total_files}",
        f"  source files: {summary.source_files}",
        f"  test files: {summary.test_files}",
        f"  docs: {summary.documentation_files}",
        f"  config files: {summary.config_files}",
        "",
        "Directories",
        f"  source: {', '.join(report.source_directories) if report.source_directories else 'none'}",
        f"  tests: {', '.join(report.test_directories) if report.test_directories else 'none'}",
        "",
        "Largest files",
    ]

    if report.largest_files:
        for stat in report.largest_files:
            lines.append(f"  - {stat.path} ({stat.size_bytes} bytes, {stat.category})")
    else:
        lines.append("  none")

    lines.append("")
    lines.append("Findings")

    if report.findings:
        for finding in report.findings:
            lines.append(f"  - [{finding.severity}] {finding.code}: {finding.message}")
    else:
        lines.append("  none")

    return "\n".join(lines)
