from __future__ import annotations

from collections import Counter
from pathlib import Path

from repolens.core.models import FileStat, Finding, ScanReport, Summary, relative_to_root

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

SOURCE_SUFFIXES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
}

DOC_FILENAMES = {"readme.md", "readme.txt", "readme"}
LICENSE_FILENAMES = {
    "license",
    "license.md",
    "license.txt",
    "copying",
    "copying.md",
    "copying.txt",
}
CONFIG_FILENAMES = {
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "go.mod",
    "cargo.toml",
    "makefile",
}
DEPENDENCY_FILENAMES = {
    "cargo.lock",
    "composer.lock",
    "go.sum",
    "package-lock.json",
    "pdm.lock",
    "pipfile",
    "pipfile.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "requirements.txt",
    "uv.lock",
    "yarn.lock",
}
PROJECT_METADATA_FILENAMES = {
    "build.gradle",
    "cargo.toml",
    "composer.json",
    "gemfile",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
}
CI_FILENAMES = {
    ".gitlab-ci.yml",
    ".gitlab-ci.yaml",
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
}


def analyze_repository(root: Path) -> ScanReport:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    files = sorted(_iter_files(root))
    file_stats = [_build_file_stat(path, root) for path in files]
    summary = _build_summary(root, file_stats)
    findings = _build_findings(root, summary, file_stats)

    return ScanReport(
        summary=summary,
        findings=findings,
        largest_files=sorted(file_stats, key=lambda stat: stat.size_bytes, reverse=True)[:5],
        source_directories=_collect_directories(file_stats, "source"),
        test_directories=_collect_directories(file_stats, "test"),
        license_files=_collect_matching_paths(file_stats, _is_license_file),
        ci_files=_collect_matching_paths(file_stats, _is_ci_file),
        dependency_files=_collect_matching_paths(file_stats, _is_dependency_file),
        project_metadata_files=_collect_matching_paths(file_stats, _is_project_metadata_file),
    )


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in IGNORED_DIRS:
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            continue

        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def _build_file_stat(path: Path, root: Path) -> FileStat:
    relative_path = Path(relative_to_root(path, root))
    size_bytes = path.stat().st_size
    return FileStat(
        path=str(relative_path),
        size_bytes=size_bytes,
        category=_categorize(relative_path),
    )


def _categorize(path: Path) -> str:
    lowered_parts = [part.lower() for part in path.parts]
    filename = path.name.lower()

    if "tests" in lowered_parts or filename.startswith("test_") or filename.endswith("_test.py"):
        return "test"
    if filename in DOC_FILENAMES or filename in LICENSE_FILENAMES or path.suffix.lower() in {".md", ".rst"}:
        return "documentation"
    if filename in CONFIG_FILENAMES or _is_dependency_file(path) or _is_ci_file(path):
        return "config"
    if path.suffix.lower() in SOURCE_SUFFIXES:
        return "source"
    return "other"


def _build_summary(root: Path, file_stats: list[FileStat]) -> Summary:
    category_counts = Counter(stat.category for stat in file_stats)
    languages = Counter()

    for stat in file_stats:
        suffix = Path(stat.path).suffix.lower()
        language = SOURCE_SUFFIXES.get(suffix)
        if language:
            languages[language] += 1

    return Summary(
        root_path=str(root),
        total_files=len(file_stats),
        source_files=category_counts["source"],
        test_files=category_counts["test"],
        documentation_files=category_counts["documentation"],
        config_files=category_counts["config"],
        dominant_language=languages.most_common(1)[0][0] if languages else "Unknown",
        layout=_detect_layout(file_stats),
    )


def _detect_layout(file_stats: list[FileStat]) -> str:
    paths = [Path(stat.path) for stat in file_stats]
    top_level_names = {path.parts[0].lower() for path in paths if path.parts}

    if "src" in top_level_names:
        return "src-layout"
    if any(path.name.lower() == "package.json" for path in paths):
        return "flat-js-layout"
    if any(path.suffix.lower() == ".py" for path in paths):
        return "flat-python-layout"
    return "unknown"


def _collect_directories(file_stats: list[FileStat], category: str) -> list[str]:
    directories = {
        str(Path(stat.path).parent)
        for stat in file_stats
        if stat.category == category and str(Path(stat.path).parent) != "."
    }
    return sorted(directories)


def _collect_matching_paths(file_stats: list[FileStat], predicate) -> list[str]:
    return sorted(stat.path for stat in file_stats if predicate(Path(stat.path)))


def _is_license_file(path: Path) -> bool:
    return path.name.lower() in LICENSE_FILENAMES


def _is_dependency_file(path: Path) -> bool:
    filename = path.name.lower()
    return filename in DEPENDENCY_FILENAMES or (
        filename.startswith("requirements") and path.suffix.lower() == ".txt"
    )


def _is_project_metadata_file(path: Path) -> bool:
    return path.name.lower() in PROJECT_METADATA_FILENAMES


def _is_ci_file(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    filename = path.name.lower()

    if filename in CI_FILENAMES:
        return True
    if len(parts) >= 3 and parts[0] == ".github" and parts[1] == "workflows":
        return path.suffix.lower() in {".yml", ".yaml"}
    if len(parts) >= 2 and parts[0] == ".circleci" and parts[1] == "config.yml":
        return True
    return False


def _build_findings(root: Path, summary: Summary, file_stats: list[FileStat]) -> list[Finding]:
    findings: list[Finding] = []
    license_files = _collect_matching_paths(file_stats, _is_license_file)
    ci_files = _collect_matching_paths(file_stats, _is_ci_file)
    dependency_files = _collect_matching_paths(file_stats, _is_dependency_file)
    project_metadata_files = _collect_matching_paths(file_stats, _is_project_metadata_file)

    readme_present = any(Path(stat.path).name.lower() in DOC_FILENAMES for stat in file_stats)
    if not readme_present:
        findings.append(
            Finding(
                code="missing-readme",
                severity="medium",
                message="Repository has no README, which makes onboarding and intent harder to understand.",
            )
        )

    if summary.source_files > 0 and summary.test_files == 0:
        findings.append(
            Finding(
                code="missing-tests",
                severity="high",
                message="Source files exist but no tests were detected.",
            )
        )

    if summary.source_files > 0 and not license_files:
        findings.append(
            Finding(
                code="missing-license",
                severity="low",
                message="Repository has source code but no license file was detected.",
            )
        )

    if summary.source_files > 0 and not project_metadata_files:
        findings.append(
            Finding(
                code="missing-project-metadata",
                severity="low",
                message="Source files exist but no common project metadata file was detected.",
            )
        )

    if dependency_files and summary.source_files > 0 and summary.test_files == 0:
        findings.append(
            Finding(
                code="dependencies-without-tests",
                severity="medium",
                message="Dependency files exist, but no tests were detected for the source code.",
            )
        )

    if summary.source_files > 0 and summary.test_files > 0 and not ci_files:
        findings.append(
            Finding(
                code="missing-ci",
                severity="low",
                message="Source and test files exist, but no common CI configuration was detected.",
            )
        )

    if summary.layout == "flat-python-layout" and summary.source_files >= 5:
        findings.append(
            Finding(
                code="consider-src-layout",
                severity="low",
                message="Python project appears to use a flat layout; a src layout can reduce import ambiguity as the codebase grows.",
            )
        )

    oversized_sources = [
        stat for stat in file_stats if stat.category == "source" and stat.size_bytes > 20_000
    ]
    for stat in oversized_sources[:3]:
        findings.append(
            Finding(
                code="large-source-file",
                severity="medium",
                message=f"{stat.path} is larger than 20 KB; it may be carrying too many responsibilities.",
            )
        )

    nested_test_dirs = {
        str(Path(stat.path).parent)
        for stat in file_stats
        if stat.category == "test" and str(Path(stat.path).parent).startswith("src/")
    }
    if nested_test_dirs:
        findings.append(
            Finding(
                code="tests-inside-src",
                severity="low",
                message="Some tests live inside src/, which can blur the boundary between production and verification code.",
            )
        )

    if not any(root.glob(".git")):
        findings.append(
            Finding(
                code="missing-git-dir",
                severity="low",
                message="This directory does not appear to be a Git repository.",
            )
        )

    return findings
