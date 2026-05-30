# GitScope Copilot Instructions

## Current Repository State

- This repository currently contains planning and design documentation rather than checked-in implementation code.
- Treat `README.md`, `doc/requirement.md`, `doc/technology_design.md`, and `doc/ui_design.md` as the source of truth for product scope, architecture, and UI behavior.
- Do not assume uncommitted tooling or runtime behavior exists unless it is added to the repository.

## Build, Test, and Lint Commands

- There are no checked-in build, test, lint, or CI commands in this repository yet.
- Do not invent `pytest`, `ruff`, `mypy`, `npm`, or similar commands unless the corresponding project files are added.
- There is no checked-in single-test command yet because no test harness or test runner configuration exists in the repository.
- The only documented command contract today is the intended CLI shape from the requirements:
  - `gitscope analyze <repo-path>`
  - `gitscope analyze <repo-path> --output report`
  - `gitscope analyze <repo-path> --branch main --since 2025-01-01 --until 2025-12-31`

## High-Level Architecture

- GitScope is designed as a local-first, offline Git repository analytics platform. The primary data source is the local Git CLI, not hosting platform APIs.
- The planned execution flow is:

```text
CLI
  -> validate repo path and filters
  -> Git adapter / collectors
  -> normalized SQLite storage
  -> analyzers
  -> report builder
  -> report.json + static HTML report
```

- The analyzer layer is intentionally split into six MVP domains:
  - repository
  - commit
  - contributor
  - branch
  - file
  - timeline
- The report viewer is a results browser, not the place where analysis is triggered. Analysis starts from the CLI.
- The HTML report should be data-driven from a unified `report.json`. Any future local Web UI or API should reuse the same analysis engine and data model instead of creating a separate pipeline.
- The planned module layout in `doc/technology_design.md` is:

```text
gitscope/
├── cli/
├── core/
│   ├── git/
│   ├── collectors/
│   ├── models/
│   ├── analyzers/
│   ├── services/
│   └── utils/
├── storage/
├── reporters/
│   ├── json/
│   └── html/
├── templates/
├── assets/
└── tests/
```

## Key Conventions

- Preserve the documented product principles in all implementation work:
  - local first
  - offline first
  - source safe
  - CLI first
  - report driven
  - extensible
- Keep collection, storage, analysis, and report generation decoupled. The docs explicitly treat these as separate layers.
- Treat the output data model as a stable contract shared across collectors, analyzers, `report.json`, and the UI.
- Keep the MVP within the six documented analysis domains. Integrations and advanced analytics such as PR/issue analysis, GitHub/GitLab integration, Hotspot, Ownership, Bus Factor, Risk, Architecture, or AI analysis are out of scope unless the product docs change.
- Preserve the report output contract:

```text
report/
├── index.html
├── report.json
└── assets/
```

- Match the UI to the fixed six-page information architecture: Overview, Commits, Contributors, Branches, Files, Timeline.
- Follow the report presentation model from the UI design: summary cards first, then chart cards and Top N tables. Prefer pre-aggregated chart data over pushing raw large datasets into the UI.
- Use explicit error handling for invalid repository paths, invalid branches, invalid time ranges, Git command failures, and unwritable output directories. Do not produce empty reports that look successful.
- Branch analytics uses a default stale-branch rule of no commits for 90 days.
- UI/report behavior should include empty states instead of blank sections and use explicit branch-status badges such as `ACTIVE`, `STALE`, `AHEAD`, and `BEHIND`.

## Playwright MCP Guidance

- If future sessions work on the HTML report viewer, prefer Playwright MCP for validating rendered behavior instead of relying only on template inspection.
- Use Playwright against generated static report output such as `report/index.html`; do not assume a live backend API exists for the MVP.
- Validate the documented six-page report structure and navigation: Overview, Commits, Contributors, Branches, Files, and Timeline.
- Check the UI patterns defined in `doc/ui_design.md`: summary cards, chart cards, Top N tables, branch-status badges, and explicit empty states.
- When testing report pages, verify that page content is driven by `report.json` and that filter metadata such as repository, branch, and time range is surfaced in the report header.
