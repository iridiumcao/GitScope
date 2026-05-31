"""Contributor analytics."""

from __future__ import annotations

from collections import defaultdict

from gitscope.core.analyzers.common import metric
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import ChartData, ChartSeries, ChartVariant, SectionData, TableColumn, TableData
from gitscope.core.utils.strings import contributor_key


class ContributorAnalyzer:
    """Build the Contributors section."""

    def analyze(self, context: AnalysisContext) -> SectionData:
        contributors = context.contributors
        commits = context.commits
        contributor_rows = sorted(
            contributors,
            key=lambda contributor: (contributor.commit_count, contributor.additions - contributor.deletions),
            reverse=True,
        )

        commits_by_hour = defaultdict(int)
        commits_by_weekday = defaultdict(int)
        commit_volume_by_contributor = defaultdict(int)
        for commit in commits:
            commits_by_hour[f"{commit.committed_at.hour:02d}:00"] += 1
            commits_by_weekday[commit.committed_at.strftime("%a")] += 1
            commit_volume_by_contributor[contributor_key(commit.author_name, commit.author_email)] += commit.additions + commit.deletions

        summary = [
            metric("contributor-total", "Contributors", str(len(contributors)), "Unique author identities in the selected scope."),
            metric("contributor-active", "Active contributors", str(sum(1 for contributor in contributors if contributor.commit_count > 0)), "Contributors with at least one commit."),
            metric(
                "contributor-top",
                "Top contributor",
                contributor_rows[0].name if contributor_rows else "N/A",
                "Based on commit count.",
            ),
            metric(
                "contributor-most-lines",
                "Most changed lines",
                contributor_rows[0].name if contributor_rows else "N/A",
                "Based on total additions plus deletions.",
            ),
        ]

        charts = [
            ChartData(
                id="contributor-hourly-activity",
                title="Hourly activity",
                description="Commits grouped by authoring hour.",
                type="bar",
                default_variant="hour",
                variants={
                    "hour": ChartVariant(
                        labels=sorted(commits_by_hour),
                        y_label="Commits",
                        series=[
                            ChartSeries(
                                name="Commits",
                                values=[commits_by_hour[label] for label in sorted(commits_by_hour)],
                                color="#0891b2",
                            )
                        ],
                    )
                },
                empty_state="No commit timestamps are available.",
            ),
            ChartData(
                id="contributor-weekday-activity",
                title="Weekday activity",
                description="Commits grouped by weekday.",
                type="bar",
                default_variant="weekday",
                variants={
                    "weekday": ChartVariant(
                        labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        y_label="Commits",
                        series=[
                            ChartSeries(
                                name="Commits",
                                values=[commits_by_weekday[label] for label in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]],
                                color="#d97706",
                            )
                        ],
                    )
                },
                empty_state="No commit timestamps are available.",
            ),
            ChartData(
                id="contributor-volume",
                title="Contributor change volume",
                description="Changed lines for the most active contributors.",
                type="bar",
                default_variant="contributors",
                variants={
                    "contributors": ChartVariant(
                        labels=[contributor.name for contributor in contributor_rows[:10]],
                        y_label="Changed lines",
                        series=[
                            ChartSeries(
                                name="Changed lines",
                                values=[
                                    commit_volume_by_contributor.get(contributor.normalized_key, 0)
                                    for contributor in contributor_rows[:10]
                                ],
                                color="#7c3aed",
                            )
                        ],
                    )
                },
                empty_state="No contributor volume is available yet.",
            ),
        ]

        tables = [
            TableData(
                id="contributor-ranking",
                title="Contributor ranking",
                description="Contributors ranked by commits, additions, and deletions.",
                columns=[
                    TableColumn(key="name", label="Contributor"),
                    TableColumn(key="email", label="Email"),
                    TableColumn(key="commits", label="Commits", align="right"),
                    TableColumn(key="additions", label="Additions", align="right"),
                    TableColumn(key="deletions", label="Deletions", align="right"),
                    TableColumn(key="last_commit_at", label="Last commit"),
                ],
                rows=[
                    {
                        "name": contributor.name,
                        "email": contributor.email,
                        "commits": contributor.commit_count,
                        "additions": contributor.additions,
                        "deletions": contributor.deletions,
                        "last_commit_at": contributor.last_commit_at.isoformat(timespec="seconds") if contributor.last_commit_at else "-",
                    }
                    for contributor in contributor_rows[:20]
                ],
                empty_state="No contributor data is available yet.",
            )
        ]

        return SectionData(
            id="contributors",
            title="Contributors",
            description="Contributor rankings and activity patterns.",
            summary=summary,
            charts=charts,
            tables=tables,
        )
