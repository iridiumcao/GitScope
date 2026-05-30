# GitScope Requirements Document

## 1. Document Purpose

This document defines the current product baseline for GitScope. It aligns the project positioning, MVP scope, functional requirements, non-functional requirements, and acceptance criteria, and serves as input for the technical design and UI design.

---

## 2. Product Positioning

### 2.1 Product Name

**GitScope**

### 2.2 Product Definition

GitScope is a **local-first, offline, developer- and engineering-team-oriented Git repository analytics platform**. By analyzing the history of a local Git repository, it generates structured data and visual reports to help users understand project evolution, team contribution patterns, code change trends, and branch activity.

### 2.3 Core Principles

- Local First: Runs locally by default and does not depend on cloud services
- Offline First: Analysis does not access external platforms by default
- Source Safe: Does not upload source code and does not require hosting platform authorization
- CLI First: Uses the command line as the primary entry point
- Report Driven: Uses reports and visualizations as the primary output
- Extensible: Leaves room in the architecture for advanced analytics and plugins

---

## 3. Target Users

### 3.1 Individual Developers

Want to quickly understand commit trends, code growth, and active time distribution in personal projects.

### 3.2 Open Source Maintainers

Want to understand contributor structure, hotspot files, branch activity, and release evolution.

### 3.3 Technical Leads / Engineering Managers

Want to observe team activity, code change density, and project evolution trends through repository history data.

### 3.4 Architects / Technical Managers

At the current stage, they mainly use the basic analysis results. In the future, they can further use advanced capabilities such as Hotspot, Ownership, Bus Factor, and Risk analysis.

---

## 4. Typical Usage Scenarios

### Scenario 1: Quick Analysis of a Local Repository

The user runs:

```bash
gitscope analyze .
```

The system outputs a report directory, and the user opens the HTML report directly to review the repository overview, commit trends, contributor rankings, and file change activity.

### Scenario 2: Analysis by Branch or Time Range

The user runs:

```bash
gitscope analyze . --branch main --since 2025-01-01 --until 2025-12-31
```

The system analyzes only the data within the target branch and time window, then generates the corresponding report.

### Scenario 3: Project Retrospective

After analyzing a repository, the user uses the timeline, contributor, and branch reports to identify concentrated development periods, key contributors, and areas that have been unmaintained for a long time.

---

## 5. Product Goals

### 5.1 MVP Goals

The MVP focuses on validating the following:

1. Whether basic Git repository analytics can produce stable, clear, and readable output.
2. Whether the CLI, analysis engine, and reporting layer can share one unified data model.
3. Whether a local offline analysis workflow can satisfy the real usage scenarios of the target users.
4. Whether the current report set is sufficient to support initial project insights.

### 5.2 MVP Success Criteria

The MVP is considered successful if all of the following are met:

1. It can analyze any local Git repository.
2. It can generate both HTML reports and JSON data.
3. The CLI runs reliably and outputs a result directory.
4. Users can complete analysis without depending on GitHub or GitLab.
5. It works on Windows, macOS, and Linux.
6. It provides a usable analysis experience for repositories with around 10,000 commits.
7. The code structure can be extended to support future advanced analysis modules.

---

## 6. MVP Scope

### 6.1 Included Scope

The MVP includes only the following six categories of analysis:

1. Repository Analytics
2. Commit Analytics
3. Contributor Analytics
4. Branch Analytics
5. File Analytics
6. Timeline Analytics

### 6.2 Excluded Scope

The following capabilities are explicitly out of scope for the MVP:

- GitHub / GitLab / Jira / SonarQube integration
- Pull Request / Issue analysis
- Ownership analysis
- Bus Factor analysis
- Hotspot analysis
- Temporal Coupling analysis
- Churn analysis
- Risk analysis
- Architecture analysis
- AI analysis
- Multi-repository aggregate analysis
- Public release of a plugin system

---

## 7. Functional Requirements

### 7.1 CLI Requirements

### FR-CLI-01 Analyze a Repository

The system must support analyzing a target Git repository through the CLI.

```bash
gitscope analyze <repo-path>
```

### FR-CLI-02 Specify an Output Directory

The system must support specifying the output directory through an option.

```bash
gitscope analyze <repo-path> --output report
```

### FR-CLI-03 Specify a Time Range

The system must support limiting the analysis time window through `--since` and `--until`.

### FR-CLI-04 Specify a Branch

The system must support limiting the analysis scope through `--branch`.

### FR-CLI-05 View Help and Version

The system must provide help and version capabilities.

### 7.2 Repository Analytics

The system must provide repository-level basic information and overall statistics, including but not limited to:

- Repository Name
- Repository Path
- First Commit Date
- Last Commit Date
- Repository Age
- Current Branch
- Default Branch
- Total Commits
- Total Contributors
- Total Branches
- Total Tags
- Total Files

The system must also provide overall growth trend views, including:

- Commit Growth
- Contributor Growth
- Monthly Commit Trend
- Monthly Contributor Trend

### 7.3 Commit Analytics

The system must provide commit-level statistics, including:

- Total Commits
- Average Commits Per Day / Week / Month
- Average Additions / Deletions
- Average Changed Files
- Largest Commits
- Smallest Commits
- Commit Trend (by day / week / month)

### 7.4 Contributor Analytics

The system must provide contributor-level statistics, including:

- Contributor List
- Commit Count
- Lines Added / Deleted
- Files Modified
- Hourly Activity Distribution
- Weekly Activity Distribution
- Commit Size Distribution

### 7.5 Branch Analytics

The system must provide branch-level statistics, including:

- Total Branches
- Local Branches
- Remote Branches
- Branch List
- Branch Age
- Ahead / Behind status
- Stale Branch Detection

The default stale rule is:

```text
No commits for 90 days
```

### 7.6 File Analytics

The system must provide file-level statistics, including:

- Most Changed Files
- Most Added Files
- Most Deleted Files
- Recently Active Files
- Inactive Files

### 7.7 Timeline Analytics

The system must provide time-based statistics, including:

- Commit Timeline (Day / Week / Month)
- Commit Heatmap (last 365 days)
- Peak Activity (Most Active Day / Week / Month)

### 7.8 Report Output

The system must output at least the following results:

```text
report/
├── index.html
├── report.json
└── assets/
```

Where:

- `index.html`: the main report entry
- `report.json`: the structured analysis data
- `assets/`: static resources such as styles, scripts, and chart dependencies

### 7.9 GUI / Report Viewing

In the MVP, the GUI is responsible for **viewing analysis results**, not for triggering analysis tasks.

The GUI must include at least:

- Dashboard / Overview
- Commits
- Contributors
- Branches
- Files
- Timeline

---

## 8. Non-Functional Requirements

### 8.1 Performance

Target performance requirements:

- Regular repositories (around 10,000 commits) should complete the main analysis within **30 seconds**
- Large repositories (around 100,000 commits) should complete analysis within **10 minutes**

### 8.2 Compatibility

The system must support:

- Windows
- macOS
- Linux

### Git Version Requirement

```text
Git 2.30+
```

### 8.3 Security and Privacy

- Source code is not uploaded by default
- External hosting platform APIs are not called by default
- Intermediate data and analysis results are stored locally by default

### 8.4 Maintainability

- Analysis modules should be independently extensible
- The output data model should remain as stable as possible
- The CLI, analysis layer, and reporting layer should be decoupled

### 8.5 Extensibility

The MVP data model and module breakdown should leave room for the following capabilities:

- Ownership
- Hotspot
- Bus Factor
- Risk
- Architecture
- Multiple report output formats

---

## 9. Constraints and Tradeoffs

### 9.1 Current Tradeoffs

- Prioritize a complete local offline analysis loop over broad platform integration
- Prioritize clear and readable reports over covering every advanced analysis at once
- Prioritize CLI and data model stability over building complex UI interactions too early

### 9.2 Product Boundary

At the current stage, GitScope is the **MVP of a Git data analytics platform**, not a code quality scanner and not a replacement for a Git hosting platform.

---

## 10. Post-MVP Priorities

The highest-priority capabilities after the MVP are:

1. Hotspot Analysis
2. Ownership Analysis
3. Bus Factor Analysis

Reasons:

- They can significantly improve product differentiation
- They align closely with the existing data foundation
- They are more practical to implement than more complex architecture analysis

---

## 11. Acceptance Criteria

The requirements for this stage are considered complete when all of the following conditions are met:

1. Users can analyze a local repository with a single CLI command.
2. The system outputs an HTML report that can be opened and JSON data that can be consumed programmatically.
3. All six MVP analysis categories are presented through clear pages or modules.
4. The report content matches the command parameters such as repository path, branch, and time range.
5. The output is usable on the three major desktop platforms.
6. There are no obvious conflicts between the requirements, technical design, and UI design documents.
