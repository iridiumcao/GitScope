# GitScope

GitScope is a **local-first, offline Git repository analytics platform** for developers and engineering teams. It analyzes the history of a local Git repository and generates structured data plus visual reports to help users understand project evolution, contribution patterns, code change trends, and branch activity.

## MVP Focus

The current MVP is designed around these principles:

- **Local First**: run locally by default
- **Offline First**: no dependency on external platforms during analysis
- **Source Safe**: no source upload and no hosting-platform authorization required
- **CLI First**: command line is the primary entry point
- **Report Driven**: HTML reports and JSON outputs are the main deliverables
- **Extensible**: architecture leaves room for advanced analytics later

The MVP covers six analysis domains:

1. Repository analytics
2. Commit analytics
3. Contributor analytics
4. Branch analytics
5. File analytics
6. Timeline analytics

## Intended Users

- Individual developers reviewing personal project history
- Open source maintainers tracking contributor and repository activity
- Technical leads and engineering managers observing project evolution and team activity

## Expected Usage

Example commands defined by the current product documents:

```bash
gitscope analyze .
gitscope analyze . --branch main --since 2025-01-01 --until 2025-12-31
```

Expected output:

```text
report/
├── index.html
├── report.json
└── assets/
```

The MVP report viewer is organized into six top-level pages:

1. Overview
2. Commits
3. Contributors
4. Branches
5. Files
6. Timeline

## Technical Baseline

The current technical design defines the following baseline:

| Topic | Decision |
| --- | --- |
| Language | Python 3.11+ |
| Git data source | Git CLI |
| CLI framework | Typer |
| Data modeling | Pydantic |
| Storage | SQLite |
| Persistence layer | SQLAlchemy |
| HTML templating | Jinja2 |
| Charts | ECharts |
| Testing | pytest |
| Future Web extension | FastAPI |

Recommended architecture flow:

```text
Git Repository
      │
      ▼
Git Adapter / Collector
      │
      ▼
Normalized Storage (SQLite)
      │
      ▼
Analyzers
      │
      ▼
Report Builder
      │
      ├── report.json
      └── HTML Report
```

## Scope Boundaries

The MVP intentionally excludes advanced or platform-integrated capabilities such as:

- GitHub / GitLab / Jira / SonarQube integration
- Pull request and issue analysis
- Ownership, Bus Factor, Hotspot, Churn, Risk, and Architecture analysis
- AI analysis
- Multi-repository aggregate analysis
- A public plugin system

Post-MVP priorities are:

1. Hotspot analysis
2. Ownership analysis
3. Bus Factor analysis

## Documentation

| Document | Purpose |
| --- | --- |
| `doc/requirement.md` | Defines the MVP goals, scope, functional requirements, non-functional requirements, and acceptance criteria |
| `doc/technology_design.md` | Defines the technical stack, architecture, data model, execution flow, and extension strategy |
| `doc/ui_design.md` | Defines the report information architecture, page layout, component rules, interaction model, and visual direction |

## Recommended Reading Order

1. Read `doc/requirement.md` to understand product scope and acceptance criteria.
2. Read `doc/technology_design.md` to understand the implementation approach and system architecture.
3. Read `doc/ui_design.md` to understand report structure and presentation rules.