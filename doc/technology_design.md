# GitScope Technical Design Document

## 1. Document Goal

This document defines the technical implementation plan for the GitScope MVP, including technology choices, system layers, core flows, data models, report generation, and extension points for future versions.

---

## 2. Design Principles

- **Local first**: Core capabilities must work locally and offline
- **CLI first**: The CLI is the primary MVP entry point
- **Data driven**: The analysis layer and presentation layer are built around a unified data model
- **Layered decoupling**: Collection, storage, analysis, and output remain independent
- **Progressive evolution**: The MVP starts with static reports for a single repository, then expands to Web, plugins, and advanced analytics

---

## 3. Technology Choices

### 3.1 Language and Runtime

- **Python 3.11+**

Reasons:

- Well suited for building CLI tools and data processing workflows quickly
- Has mature packaging, testing, and Web ecosystems
- Makes it easier to support CLI usage, library usage, and Web services in the future

### 3.2 Git Data Source

- **Git CLI**

The core idea is to collect data by calling local Git commands directly instead of relying on hosting platform APIs. Recommended commands include:

- `git log`
- `git shortlog`
- `git branch`
- `git for-each-ref`
- `git rev-list`
- `git ls-tree`
- `git show`
- `git tag`

### 3.3 CLI Framework

- **Typer**

Reasons:

- Easy to define commands and parameters
- Works naturally with Python type hints
- Well suited for building clear developer-focused CLIs

### 3.4 Data Modeling and Validation

- **Pydantic**

Used for:

- Modeling collector output structures
- Constraining analyzer inputs and outputs
- Serializing report JSON

### 3.5 Data Storage

- **SQLite**
- Recommended Python ORM / query layer: **SQLAlchemy**

Reasons:

- Lightweight, zero-deployment, and cross-platform
- Suitable for local analysis caching and result persistence
- Makes it easier to support incremental analysis and advanced analyzers later

### 3.6 HTML Reporting Layer

- **Jinja2**: HTML template rendering
- **Local JavaScript + SVG renderer**: chart rendering inside the static report

Reasons:

- Jinja2 is well suited for generating static HTML reports
- A local renderer keeps the report fully offline and self-contained when opened directly from the file system
- The chart payload remains reusable, so a future ECharts-based renderer can be introduced without changing the analysis pipeline

### 3.7 Testing

- **pytest**

Used for:

- Collector command parsing tests
- Analyzer statistics tests
- CLI parameter tests
- Report output structure tests

### 3.8 Web Extension Point

The MVP does not require a local service, but future versions can introduce:

- **FastAPI**: local service / API layer

This should reuse the existing analysis engine and data model.

---

## 4. Overall Architecture

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
      ├── Repository Analyzer
      ├── Commit Analyzer
      ├── Contributor Analyzer
      ├── Branch Analyzer
      ├── File Analyzer
      └── Timeline Analyzer
      │
      ▼
Report Builder
      │
      ├── report.json
      └── HTML Report
```

### 4.1 Layer Description

#### Git Adapter / Collector

Responsible for interacting with the Git repository, collecting raw data, and converting it into a unified structure.

#### Normalized Storage

Responsible for storing base entities and intermediate results to avoid rescanning the repository repeatedly.

#### Analyzers

Responsible for computing metrics and chart data for different topics.

#### Report Builder

Responsible for exporting analysis results as JSON and HTML reports.

---

## 5. Module Breakdown

The recommended code structure is:

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

### 5.1 `cli/`

Responsible for command entry points and argument parsing.

### 5.2 `core/git/`

Responsible for executing Git commands, handling repository paths, and normalizing error output.

### 5.3 `core/collectors/`

Responsible for converting raw Git output into structured records.

### 5.4 `core/models/`

Defines domain models, DTOs, and analysis result structures.

### 5.5 `core/analyzers/`

Outputs metrics, tables, and chart-ready data by topic.

### 5.6 `storage/`

Responsible for SQLite connections, table definitions, transactions, and cache strategy.

### 5.7 `reporters/`

Responsible for exporting analysis results to JSON and HTML.

---

## 6. Core Execution Flow

### 6.1 Analysis Command Flow

```text
User runs CLI
    ▼
Validate repo path and parameters
    ▼
Collect Git raw data
    ▼
Normalize and store data
    ▼
Run analyzers
    ▼
Assemble report payload
    ▼
Generate report.json and index.html
```

### 6.2 Parameter Handling Rules

### `repo-path`

- Required
- Must be a local Git repository path

### `--output`

- Optional
- Defaults to `report/`

### `--branch`

- Optional
- Limits the analysis scope

### `--since` / `--until`

- Optional
- Limit the commit time window

---

## 7. Data Model Design

### 7.1 Core Entities

The MVP should include at least the following tables:

### `repositories`

Stores basic information about the analyzed repository.

Suggested fields:

- `id`
- `name`
- `path`
- `current_branch`
- `default_branch`
- `first_commit_at`
- `last_commit_at`
- `created_at`
- `updated_at`

### `contributors`

Stores basic contributor information.

Suggested fields:

- `id`
- `name`
- `email`
- `normalized_key`

### `commits`

Stores basic commit information.

Suggested fields:

- `sha`
- `repository_id`
- `author_id`
- `author_name`
- `author_email`
- `committed_at`
- `message`
- `parents_count`
- `additions`
- `deletions`
- `changed_files`
- `branch_hint`

### `branches`

Stores branch information.

Suggested fields:

- `id`
- `repository_id`
- `name`
- `is_local`
- `is_remote`
- `head_sha`
- `last_commit_at`
- `ahead_count`
- `behind_count`

### `files`

Stores basic file information.

Suggested fields:

- `id`
- `repository_id`
- `path`
- `extension`
- `first_seen_at`
- `last_seen_at`

### `commit_files`

Stores relationships between commits and files.

Suggested fields:

- `commit_sha`
- `file_id`
- `change_type`
- `additions`
- `deletions`

### `tags`

Stores basic tag information as a placeholder for future release analysis.

### 7.2 Result Data Model

Analyzer output should follow a unified structure:

```json
{
  "metadata": {},
  "summary": {},
  "charts": [],
  "tables": [],
  "sections": []
}
```

Benefits:

- Easy JSON output
- Easy HTML template rendering
- Easy future Web API support

---

## 8. Analyzer Design

### 8.1 Repository Analyzer

Outputs:

- Basic repository information
- Overall size metrics
- Growth trends

### 8.2 Commit Analyzer

Outputs:

- Total commit count
- Average commit frequency
- Commit size statistics
- Largest / smallest commit rankings

### 8.3 Contributor Analyzer

Outputs:

- Contributor list
- Individual statistics
- Active time distribution
- Commit size distribution

### 8.4 Branch Analyzer

Outputs:

- Branch summary
- Branch list
- Ahead / Behind
- Stale branches

### 8.5 File Analyzer

Outputs:

- Top Changed Files
- Top Added Files
- Top Deleted Files
- Recently Active Files
- Inactive Files

### 8.6 Timeline Analyzer

Outputs:

- Commit Timeline
- Commit Heatmap
- Peak Activity

---

## 9. HTML Report Design

### 9.1 Output Structure

```text
report/
├── index.html
├── report.json
└── assets/
```

### `report.json`

Acts as the unified data output for:

- HTML template consumption
- Secondary development
- Automated processing

### `index.html`

Acts as the main entry page and is responsible for organizing navigation, layout, and chart mounting.

### 9.2 Rendering Strategy

The MVP should use:

1. Python to generate `report.json`
2. Python to generate the base HTML shell
3. Front-end scripts to read the report payload and render charts and tables

For local `file://` compatibility, `index.html` may embed the same payload that is written to `report.json`, as long as `report.json` remains the canonical machine-readable report output.

Benefits of this approach:

- Clear template structure
- Decoupled chart logic and data structure
- Lower reuse cost when evolving to a local Web service later

---

## 10. Error Handling Design

The system should clearly distinguish the following error types:

- Invalid repository path
- Target directory is not a Git repository
- Git command execution failure
- Target branch does not exist
- Invalid time range parameters
- Output directory is not writable

Handling principles:

- Return clear error reasons in the CLI
- Do not swallow critical exceptions
- Do not generate an empty report that looks successful

---

## 11. Performance Design

### 11.1 Optimization Directions

- Read Git data in batches whenever possible to reduce command count
- Write reusable base data into SQLite
- Run analyzers on normalized data instead of repeatedly calling Git
- Control Top N, pagination, and chart data granularity for large repositories

### 11.2 Recommended Strategies

- Store commit details separately from commit-file relationships
- Output heatmaps and trend charts from pre-aggregated results
- Show Top N by default in tables to avoid overloading a single page

---

## 12. Extensibility Design

The MVP should reserve extension points for future capabilities:

### 12.1 New Analyzer Extension

When adding `HotspotAnalyzer`, `OwnershipAnalyzer`, or `BusFactorAnalyzer` in the future, it should only require:

1. Adding the necessary collector data
2. Adding the new analyzer
3. Registering the new module in the Report Builder

### 12.2 Multiple Output Formats

Current outputs:

- JSON
- HTML

Future outputs can include:

- REST API
- Local Web dashboard
- Exported images / PDF

### 12.3 Multiple Data Sources

Current data source:

- Git CLI

Future data sources can include:

- GitHub
- GitLab
- Jira
- SonarQube

---

## 13. Release and Delivery Path

### MVP Delivery

- Publish as a **Python package**
- Users obtain the CLI through `pip install gitscope`

### Future Evolution

1. V1: Python package + CLI + HTML report
2. V2: Local Web dashboard
3. V3: Plugin system
4. V4: Docker / team deployment

---

## 14. Technical Decision Summary

The key technical decisions at the current stage are:

| Topic | Decision |
| --- | --- |
| Programming language | Python 3.11+ |
| Data source | Git CLI |
| CLI | Typer |
| Data modeling | Pydantic |
| Data storage | SQLite |
| Persistence access | SQLAlchemy |
| HTML templating | Jinja2 |
| Charts | ECharts |
| Testing | pytest |
| Web extension | FastAPI |

These decisions serve one goal: **complete a stable local offline analysis loop first, then evolve gradually into an extensible Git data analytics platform.**
