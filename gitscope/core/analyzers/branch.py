"""Branch analytics."""

from __future__ import annotations

from gitscope.core.analyzers.common import STALE_BRANCH_DAYS, humanized_age_label, metric
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import SectionData, TableColumn, TableData
from gitscope.core.utils.time import days_between


class BranchAnalyzer:
    """Build the Branches section."""

    def analyze(self, context: AnalysisContext) -> SectionData:
        branches = context.branches
        now = context.generated_at
        stale_count = 0
        rows = []
        for branch in branches:
            badges: list[str] = []
            if branch.last_commit_at and days_between(branch.last_commit_at, now) >= STALE_BRANCH_DAYS:
                badges.append("STALE")
                stale_count += 1
            else:
                badges.append("ACTIVE")
            if branch.ahead_count > 0:
                badges.append("AHEAD")
            if branch.behind_count > 0:
                badges.append("BEHIND")

            rows.append(
                {
                    "name": branch.name,
                    "type": "remote" if branch.is_remote else "local",
                    "last_commit_at": branch.last_commit_at.isoformat(timespec="seconds") if branch.last_commit_at else "-",
                    "age": humanized_age_label(branch.first_unique_commit_at or branch.last_commit_at, now),
                    "ahead": branch.ahead_count,
                    "behind": branch.behind_count,
                    "status": badges,
                }
            )

        rows.sort(key=lambda row: (row["type"], row["name"]))

        summary = [
            metric("branch-total", "Branches", str(len(branches)), "Local and remote refs."),
            metric("branch-local", "Local branches", str(sum(1 for branch in branches if branch.is_local)), "refs/heads"),
            metric("branch-remote", "Remote branches", str(sum(1 for branch in branches if branch.is_remote)), "refs/remotes"),
            metric("branch-stale", "Stale branches", str(stale_count), f"No commits for at least {STALE_BRANCH_DAYS} days."),
            metric("branch-default", "Default branch", context.repository.default_branch or "N/A", "Best-effort detection."),
        ]

        tables = [
            TableData(
                id="branch-status",
                title="Branch status",
                description="Ahead/behind counts, staleness, and branch age.",
                columns=[
                    TableColumn(key="name", label="Branch"),
                    TableColumn(key="type", label="Type"),
                    TableColumn(key="last_commit_at", label="Last commit"),
                    TableColumn(key="age", label="Age"),
                    TableColumn(key="ahead", label="Ahead", align="right"),
                    TableColumn(key="behind", label="Behind", align="right"),
                    TableColumn(key="status", label="Status"),
                ],
                rows=rows,
                empty_state="No branches were found in this repository.",
            )
        ]

        return SectionData(
            id="branches",
            title="Branches",
            description="Branch health, ahead/behind status, and stale branch detection.",
            summary=summary,
            charts=[],
            tables=tables,
        )
