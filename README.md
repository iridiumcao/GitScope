# GitScope

GitScope is a **local-first, offline Git repository analytics platform** for developers and engineering teams. It analyzes a local Git repository with the Git CLI, normalizes data into SQLite, and generates a static HTML + JSON report.

## Current MVP

The current implementation covers the six documented MVP analysis domains:

1. Overview
2. Commits
3. Contributors
4. Branches
5. Files
6. Timeline

The report output contract is:

```text
report/
├── index.html
├── report.json
└── assets/
```

## Quick Start

Install the package in editable mode:

```bash
python3 -m pip install -e .
```

Generate a report for the current repository:

```bash
gitscope analyze .
gitscope analyze . --output report
gitscope analyze . --branch main --since 2025-01-01 --until 2025-12-31
```

Run the test suite:

```bash
python3 -m pytest
```

## Implementation Notes

| Topic | Current implementation |
| --- | --- |
| Language | Python 3.11+ |
| CLI | Typer |
| Git data source | Local Git CLI |
| Modeling | Pydantic |
| Storage | In-memory SQLite via SQLAlchemy during each analysis run |
| HTML report | Jinja2 shell + local JavaScript/SVG renderer |
| Testing | pytest |

The HTML report is driven by the same unified data model written to `report.json`. For local `file://` viewing, `index.html` embeds the same payload so the static report works without a web server.

## Product Principles

- **Local First**: run locally by default
- **Offline First**: analysis does not depend on external platforms
- **Source Safe**: no source upload and no hosting-platform authorization
- **CLI First**: analysis starts from the command line
- **Report Driven**: HTML and JSON are the primary outputs
- **Extensible**: the module layout is ready for future analyzers

## Documentation

| Document | Purpose |
| --- | --- |
| `doc/requirement.md` | MVP goals, scope, requirements, non-functional constraints, and acceptance criteria |
| `doc/technology_design.md` | Stack choices, architecture, data model, execution flow, and extension strategy |
| `doc/ui_design.md` | Report information architecture, page layout, and UI behavior |

When implementation changes affect documented behavior, update the related docs in the same task so code and documentation stay aligned.
