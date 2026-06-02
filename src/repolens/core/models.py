from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileStat:
    path: str
    size_bytes: int
    category: str


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class Summary:
    root_path: str
    total_files: int
    source_files: int
    test_files: int
    documentation_files: int
    config_files: int
    dominant_language: str
    layout: str


@dataclass(frozen=True)
class ScanReport:
    summary: Summary
    findings: list[Finding]
    largest_files: list[FileStat]
    source_directories: list[str]
    test_directories: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
