# repo-lens

`repo-lens` is a small CLI for inspecting repository structure and surfacing a few engineering signals.

This version is intentionally simple and learning-oriented:

- `scan` walks a repository
- analyzers produce a typed report
- formatters render text or JSON output
- tests exercise the analysis layer without depending on the terminal UI

The scanner currently surfaces:

- source, test, documentation, and config counts
- common source and test directories
- license, CI, dependency, and project metadata files
- findings for missing onboarding or project-hygiene signals

## Run locally

```bash
PYTHONPATH=src python3 -m repolens scan .
```

```bash
PYTHONPATH=src python3 -m repolens --version
```

## Run tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
