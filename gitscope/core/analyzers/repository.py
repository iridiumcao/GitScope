"""Repository overview analyzer."""

from __future__ import annotations

from datetime import datetime

from gitscope.core.analyzers.common import build_commit_trend_variants, humanized_age_label, metric
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import ChartData, ChartSeries, ChartVariant, SectionData, TableColumn, TableData


class RepositoryAnalyzer:
    """Build the Overview section."""

    def analyze(self, context: AnalysisContext) -> SectionData:
        now = context.generated_at
        commits = context.commits
        contributors = context.contributors
        branches = context.branches
        files = context.files

        summary = [
            metric(
                "repo-age",
                "Repository age",
                humanized_age_label(context.repository.first_commit_at, context.repository.last_commit_at or now),
                "From first to latest analyzed commit.",
            ),
            metric("total-commits", "Commits", str(len(commits)), "Within the selected analysis scope."),
            metric("contributors", "Contributors", str(len(contributors)), "Unique author name/email pairs."),
            metric("branches", "Branches", str(len(branches)), "Local and remote refs discovered from Git."),
            metric("tags", "Tags", str(len(context.tags)), "Annotated and lightweight tags."),
            metric("files", "Current files", str(context.repository.total_files), "Files present at the analyzed ref."),
        ]

        top_contributors = sorted(
            contributors,
            key=lambda contributor: (contributor.commit_count, contributor.additions - contributor.deletions),
            reverse=True,
        )[:10]
        top_files = sorted(files, key=lambda file_record: (file_record.change_count, file_record.last_seen_at or datetime.min), reverse=True)[:10]

        active_contributor_counts: dict[str, set[str]] = {}
        for commit in commits:
            label = commit.committed_at.strftime("%Y-%m")
            active_contributor_counts.setdefault(label, set()).add(f"{commit.author_name}<{commit.author_email}>")

        contributor_growth_labels = sorted(active_contributor_counts)
        contributor_growth = ChartVariant(
            labels=contributor_growth_labels,
            y_label="Contributors",
            series=[
                ChartSeries(
                    name="Active contributors",
                    values=[len(active_contributor_counts[label]) for label in contributor_growth_labels],
                    color="#f97316",
                )
            ],
        )

        charts = [
            ChartData(
                id="overview-commit-trend",
                title="Commit trend",
                description="Daily, weekly, and monthly commit movement for the selected scope.",
                type="line",
                default_variant="month",
                variants=build_commit_trend_variants(commits),
                empty_state="No commits were found for the selected scope.",
            ),
            ChartData(
                id="overview-contributor-activity",
                title="Contributor activity",
                description="Active contributor counts by month.",
                type="bar",
                default_variant="month",
                variants={"month": contributor_growth},
                empty_state="No contributor activity is available yet.",
            ),
        ]

        tables = [
            TableData(
                id="overview-top-contributors",
                title="Top contributors",
                description="Contributors ranked by commit count.",
                columns=[
                    TableColumn(key="name", label="Contributor"),
                    TableColumn(key="commits", label="Commits", align="right"),
                    TableColumn(key="additions", label="Additions", align="right"),
                    TableColumn(key="deletions", label="Deletions", align="right"),
                    TableColumn(key="last_commit_at", label="Last commit"),
                ],
                rows=[
                    {
                        "name": contributor.name,
                        "commits": contributor.commit_count,
                        "additions": contributor.additions,
                        "deletions": contributor.deletions,
                        "last_commit_at": contributor.last_commit_at.isoformat(timespec="seconds") if contributor.last_commit_at else "-",
                    }
                    for contributor in top_contributors
                ],
                empty_state="No contributors are available yet.",
            ),
            TableData(
                id="overview-top-files",
                title="Most changed files",
                description="Files with the highest number of recorded modifications.",
                columns=[
                    TableColumn(key="path", label="File"),
                    TableColumn(key="changes", label="Changes", align="right"),
                    TableColumn(key="additions", label="Additions", align="right"),
                    TableColumn(key="deletions", label="Deletions", align="right"),
                    TableColumn(key="last_seen_at", label="Last touched"),
                ],
                rows=[
                    {
                        "path": file_record.path,
                        "changes": file_record.change_count,
                        "additions": file_record.additions,
                        "deletions": file_record.deletions,
                        "last_seen_at": file_record.last_seen_at.isoformat(timespec="seconds") if file_record.last_seen_at else "-",
                    }
                    for file_record in top_files
                ],
                empty_state="No file history is available yet.",
            ),
        ]

        notes = []
        if not context.tags:
            notes.append("No tags were found. Release-oriented reporting will show empty states until tags are added.")

        return SectionData(
            id="overview",
            title="Overview",
            description="Repository-level summary cards, trend charts, and top lists.",
            summary=summary,
            charts=charts,
            tables=tables,
            notes=notes,
        )
