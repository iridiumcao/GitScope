# GitScope UI Design Document

## 1. Document Goal

This document defines the information architecture, page layout, component conventions, interaction rules, and visual direction for the GitScope MVP reporting interface, so the HTML report and future local GUI can share a consistent experience.

---

## 2. Design Goals

The GitScope MVP UI is not a complex operations console. It is a **developer-oriented analysis result viewer**.

Design goals:

1. Help users understand repository status quickly
2. Make core trends, rankings, and anomalies obvious at a glance
3. Keep the page structure aligned with CLI output
4. Reuse the same information architecture for static HTML and future local Web interfaces

---

## 3. Target Users and Usage Flow

### 3.1 Target Users

- Individual developers
- Open source project maintainers
- Technical leads

### 3.2 Usage Flow

The typical flow is:

1. The user runs `gitscope analyze`
2. The system generates `report/index.html`
3. The user opens the report in a browser
4. The user navigates through Overview, Commits, Contributors, Branches, Files, and Timeline from the sidebar

---

## 4. Information Architecture

The MVP should use **6 top-level pages**:

1. Overview
2. Commits
3. Contributors
4. Branches
5. Files
6. Timeline

### 4.1 Page Responsibilities

| Page | Responsibility |
| --- | --- |
| Overview | Show the overall repository status and key summary |
| Commits | Show commit volume, commit trends, and commit size statistics |
| Contributors | Show contributor rankings, activity, and contributor profiles |
| Branches | Show the branch list, branch status, and stale branches |
| Files | Show file change hotspots and active files |
| Timeline | Show time-based trends and heatmaps |

---

## 5. Overall Layout

The recommended layout is a classic analytics dashboard:

```text
┌─────────────────────────────────────────────┐
│ Top Bar                                     │
├───────────────┬─────────────────────────────┤
│ Sidebar       │ Main Content                │
│               │                             │
│ Overview      │ Summary Cards               │
│ Commits       │ Chart Cards                 │
│ Contributors  │ Tables                      │
│ Branches      │ Detail Sections             │
│ Files         │                             │
│ Timeline      │                             │
└───────────────┴─────────────────────────────┘
```

### 5.1 Top Bar

Displays:

- Product name: GitScope
- Current repository name
- Analysis time range
- Current branch / filter conditions

### 5.2 Sidebar

Responsibilities:

- Page navigation
- Current page highlight
- Quick navigation within long reports

### 5.3 Main Content

Displayed in page sections such as:

- Summary Cards
- Chart Cards
- Data Tables
- Insight Blocks

---

## 6. Page Design

### 6.1 Overview Page

### Page Goal

Help users understand the overall repository status within 30 seconds.

### Page Structure

1. Repository header section
2. Core summary card section
3. Trend chart section
4. Quick ranking section

### Key Modules

#### Basic Information Cards

Recommended fields:

- Repository Name
- Repository Path
- First Commit Date
- Last Commit Date
- Repository Age
- Current Branch
- Default Branch

#### Core Metric Cards

Recommended fields:

- Total Commits
- Total Contributors
- Total Branches
- Total Tags
- Total Files

#### Trend Charts

- Monthly Commit Trend
- Monthly Contributor Trend

#### Quick Rankings

- Top Contributors
- Most Changed Files

### 6.2 Commits Page

### Page Goal

Help users understand commit frequency and commit size.

### Key Modules

- Commit Summary Cards
- Commit Trend Chart (Day / Week / Month toggle)
- Largest Commits Table
- Smallest Commits Table
- Commit Size Distribution Chart

### 6.3 Contributors Page

### Page Goal

Help users identify key contributors and activity patterns.

### Key Modules

- Contributor Ranking Table
- Contributor Detail Panel
- Hourly Activity Chart
- Weekly Activity Chart
- Commit Size Distribution Chart

### Interaction Recommendations

- When a contributor is clicked in the table, expand the detail section on the right side or below
- In a static report, this can be implemented with in-page anchors or collapsible cards

### 6.4 Branches Page

### Page Goal

Help users understand branch status and maintenance condition.

### Key Modules

- Branch Summary Cards
- Branch List Table
- Ahead / Behind Status
- Stale Branch Section

### Status Labels

- `ACTIVE`
- `STALE`
- `AHEAD`
- `BEHIND`

Status should be clearly distinguished through badges.

### 6.5 Files Page

### Page Goal

Help users find the most active files, the most frequently changed files, and files that have not been maintained for a long time.

### Key Modules

- Most Changed Files Table
- Most Added Files Table
- Most Deleted Files Table
- Recently Active Files
- Inactive Files

### 6.6 Timeline Page

### Page Goal

Help users understand project evolution through time-based patterns.

### Key Modules

- Commit Timeline Chart
- Commit Heatmap
- Peak Activity Cards

---

## 7. Component Conventions

### 7.1 Summary Card

Suitable for presenting a single key metric.

Recommended structure:

- Label
- Value
- Optional Delta / Hint

Example:

```text
Total Commits
12,548
```

### 7.2 Chart Card

Used to contain charts.

Recommended structure:

- Title
- Description
- Chart Area
- Optional Toolbar

### Toolbar Capabilities

- Time granularity switching
- Export PNG
- Fullscreen view

### 7.3 Data Table

Used to contain rankings, lists, and details.

Minimum support:

- Clear column headers
- Right-aligned numeric values
- Truncated display for long paths
- Top N limits

Recommended support:

- Sorting
- Filtering
- Search

### 7.4 Badge

Used to represent status, such as:

- Branch Status
- Recent / Inactive
- Current Branch

---

## 8. Interaction Design

### 8.1 Page Navigation

- The top-level sidebar navigation remains visible
- The current page is highlighted
- Long pages can support section anchors

### 8.2 Chart Interaction

Chart interaction should enhance readability and should not become overly complex.

Recommended MVP support:

- Hover tooltip
- Legend show / hide
- Data zoom
- PNG export

### 8.3 Table Interaction

- Highlight the current row on hover
- Support copying file paths
- Truncate SHA display while allowing full value on hover

### 8.4 Empty State

If a module has no data, the UI should display a clear empty state instead of a blank area.

Examples:

- No commits in the current time range
- No remote branches in the current repository
- No tags detected

### 8.5 Error State

If report generation is incomplete, the page should show a clear notice at the top, for example:

- Partial data collection failed
- The current chart is unavailable

---

## 9. Visual Design Direction

### 9.1 Style Keywords

- Clean
- Professional
- Developer Friendly
- Data Focused

### 9.2 Color Recommendations

Use balanced neutral tones and avoid excessive decoration.

### Primary Color

- Blue tones: for primary navigation, main trend charts, and interactive controls

### Secondary Colors

- Green: positive / active
- Orange: warning / stale
- Red: risk / anomaly
- Gray: neutral information

### 9.3 Typography and Density

- Body text: prefer system fonts
- Tables: keep numbers aligned and easy to scan
- Information density can be relatively high, but spacing and grouping must remain clear

---

## 10. Responsiveness and Adaptation

Although the MVP mainly targets desktop, it should still provide basic responsive support:

### Desktop

- Primary target scenario
- Sidebar always visible
- Multi-column chart layout

### Tablet

- Collapsible sidebar
- Charts switch to a single-column layout

### Mobile

Only basic readability needs to be guaranteed. It is not a core MVP optimization target.

---

## 11. Accessibility and Internationalization

### 11.1 Accessibility

The UI should meet at least the following:

- Charts and status indicators include text descriptions
- Color is not the only information carrier
- Table headers are clear

### 11.2 Internationalization

The MVP can start with a single-language output, but the UI structure should avoid hardcoding copy in script logic so Chinese and English switching can be supported later.

---

## 12. Alignment Requirements with the Technical Design

The UI design should follow these technical constraints:

1. Pages must consume a unified `report.json`
2. ECharts should be the preferred charting library
3. The page structure must support static HTML output
4. The MVP display must not depend on a real-time backend API

---

## 13. UI Delivery Baseline

When the following are all clear, the project can move into prototyping or front-end implementation:

1. The information architecture of the six top-level pages is fixed
2. The Summary / Chart / Table sections for each page are clearly defined
3. The layout, status labels, and empty-state conventions are unified
4. The mapping between `report.json` and page components is clear

That means the GitScope MVP UI has a stable implementation boundary.
