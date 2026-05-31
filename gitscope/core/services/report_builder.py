"""Compose the final report document from analyzer outputs."""

from __future__ import annotations

from gitscope.core.analyzers.branch import BranchAnalyzer
from gitscope.core.analyzers.commit import CommitAnalyzer
from gitscope.core.analyzers.contributor import ContributorAnalyzer
from gitscope.core.analyzers.file import FileAnalyzer
from gitscope.core.analyzers.repository import RepositoryAnalyzer
from gitscope.core.analyzers.timeline import TimelineAnalyzer
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import ReportDocument, ReportMetadata


class ReportBuilder:
    """Create the unified report document."""

    def build(self, context: AnalysisContext) -> ReportDocument:
        """Run analyzers and return a serializable report."""

        sections = [
            RepositoryAnalyzer().analyze(context),
            CommitAnalyzer().analyze(context),
            ContributorAnalyzer().analyze(context),
            BranchAnalyzer().analyze(context),
            FileAnalyzer().analyze(context),
            TimelineAnalyzer().analyze(context),
        ]
        overview = sections[0]
        return ReportDocument(
            metadata=ReportMetadata(
                generated_at=context.generated_at.isoformat(timespec="seconds"),
                repository_name=context.repository.name,
                repository_path=context.repository.path,
                analyzed_ref=context.repository.analyzed_ref,
                current_branch=context.repository.current_branch,
                default_branch=context.repository.default_branch,
                filters={
                    "branch": context.request.branch,
                    "since": context.request.since,
                    "until": context.request.until,
                },
                warnings=[],
            ),
            summary=overview.summary,
            charts=overview.charts,
            tables=overview.tables,
            sections=sections,
        )
