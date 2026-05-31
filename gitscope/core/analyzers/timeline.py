"""Timeline analytics."""

from __future__ import annotations

from gitscope.core.analyzers.common import build_commit_trend_variants, build_heatmap, metric, summarize_peak_period
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import ChartData, SectionData


class TimelineAnalyzer:
    """Build the Timeline section."""

    def analyze(self, context: AnalysisContext) -> SectionData:
        commits = context.commits
        peak_day_label, peak_day_value = summarize_peak_period(commits, "day")
        peak_week_label, peak_week_value = summarize_peak_period(commits, "week")
        peak_month_label, peak_month_value = summarize_peak_period(commits, "month")

        summary = [
            metric("timeline-peak-day", "Peak day", peak_day_label, f"{peak_day_value} commits"),
            metric("timeline-peak-week", "Peak week", peak_week_label, f"{peak_week_value} commits"),
            metric("timeline-peak-month", "Peak month", peak_month_label, f"{peak_month_value} commits"),
        ]

        charts = [
            ChartData(
                id="timeline-trend",
                title="Timeline trend",
                description="Commit volume over time with multiple granularities.",
                type="line",
                default_variant="month",
                variants=build_commit_trend_variants(commits),
                empty_state="No commit history is available for the selected scope.",
            ),
            ChartData(
                id="timeline-heatmap",
                title="Commit heatmap",
                description="Commit density by ISO week and weekday.",
                type="heatmap",
                heatmap=build_heatmap(commits),
                empty_state="No commit timestamps are available for the heatmap.",
            ),
        ]

        return SectionData(
            id="timeline",
            title="Timeline",
            description="High-level trends and commit activity heatmap.",
            summary=summary,
            charts=charts,
            tables=[],
        )
