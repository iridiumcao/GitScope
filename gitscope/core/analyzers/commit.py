"""Commit analytics."""

from __future__ import annotations

from datetime import datetime

from gitscope.core.analyzers.common import build_commit_trend_variants, commit_size_buckets, metric, safe_average, time_span_days
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import ChartData, SectionData, TableColumn, TableData


class CommitAnalyzer:
    """Build the Commits section."""

    def analyze(self, context: AnalysisContext) -> SectionData:
        commits = context.commits
        span_days = time_span_days(commits, context.generated_at)
        total_additions = sum(commit.additions for commit in commits)
        total_deletions = sum(commit.deletions for commit in commits)
        total_files = sum(commit.changed_files for commit in commits)

        summary = [
            metric("commit-total", "Total commits", str(len(commits)), "Matching the selected branch and time filters."),
            metric("commit-rate-day", "Avg/day", f"{safe_average(len(commits), span_days):.2f}", "Average commits per active day."),
            metric("commit-rate-week", "Avg/week", f"{safe_average(len(commits), max(span_days / 7, 1)):.2f}", "Average commits per active week."),
            metric("commit-rate-month", "Avg/month", f"{safe_average(len(commits), max(span_days / 30, 1)):.2f}", "Average commits per active month."),
            metric("avg-additions", "Avg additions", f"{safe_average(total_additions, len(commits)):.1f}", "Per commit."),
            metric("avg-changed-files", "Avg files changed", f"{safe_average(total_files, len(commits)):.1f}", "Per commit."),
        ]

        largest_commits = sorted(commits, key=lambda commit: (commit.additions + commit.deletions, commit.committed_at), reverse=True)[:10]
        recent_commits = sorted(commits, key=lambda commit: commit.committed_at, reverse=True)[:10]

        charts = [
            ChartData(
                id="commit-trend",
                title="Commit trend",
                description="Commit, additions, and deletions over time.",
                type="line",
                default_variant="month",
                variants=build_commit_trend_variants(commits),
                empty_state="No commit history is available for the selected scope.",
            ),
            ChartData(
                id="commit-size-distribution",
                title="Commit size distribution",
                description="Count of commits grouped by changed lines.",
                type="bar",
                default_variant="buckets",
                variants={"buckets": commit_size_buckets(commits)},
                empty_state="No commits are available to bucket yet.",
            ),
        ]

        tables = [
            TableData(
                id="commit-largest",
                title="Largest commits",
                description="Commits ranked by total changed lines.",
                columns=[
                    TableColumn(key="sha", label="SHA"),
                    TableColumn(key="author", label="Author"),
                    TableColumn(key="changed_lines", label="Changed lines", align="right"),
                    TableColumn(key="files", label="Files", align="right"),
                    TableColumn(key="committed_at", label="Committed at"),
                    TableColumn(key="message", label="Message"),
                ],
                rows=[
                    {
                        "sha": commit.sha[:10],
                        "author": commit.author_name,
                        "changed_lines": commit.additions + commit.deletions,
                        "files": commit.changed_files,
                        "committed_at": commit.committed_at.isoformat(timespec="seconds"),
                        "message": commit.message,
                    }
                    for commit in largest_commits
                ],
                empty_state="No commits are available yet.",
            ),
            TableData(
                id="commit-recent",
                title="Recent commits",
                description="Latest commits in the selected scope.",
                columns=[
                    TableColumn(key="sha", label="SHA"),
                    TableColumn(key="author", label="Author"),
                    TableColumn(key="committed_at", label="Committed at"),
                    TableColumn(key="additions", label="Additions", align="right"),
                    TableColumn(key="deletions", label="Deletions", align="right"),
                    TableColumn(key="message", label="Message"),
                ],
                rows=[
                    {
                        "sha": commit.sha[:10],
                        "author": commit.author_name,
                        "committed_at": commit.committed_at.isoformat(timespec="seconds"),
                        "additions": commit.additions,
                        "deletions": commit.deletions,
                        "message": commit.message,
                    }
                    for commit in recent_commits
                ],
                empty_state="No commits are available yet.",
            ),
        ]

        return SectionData(
            id="commits",
            title="Commits",
            description="Commit volume, size distribution, and notable commit tables.",
            summary=summary,
            charts=charts,
            tables=tables,
        )
