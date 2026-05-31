"""Shared analyzer helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import ceil

from gitscope.core.models.domain import CommitRecord
from gitscope.core.models.report import ChartSeries, ChartVariant, HeatmapCell, SummaryMetric
from gitscope.core.utils.time import days_between, format_iso

STALE_BRANCH_DAYS = 90


def metric(metric_id: str, label: str, value: str, hint: str | None = None, tone: str = "default") -> SummaryMetric:
    """Create a summary metric."""

    return SummaryMetric(id=metric_id, label=label, value=value, hint=hint, tone=tone)


def safe_average(total: int | float, count: int | float) -> float:
    """Avoid division by zero when computing averages."""

    if not count:
        return 0.0
    return total / count


def time_span_days(commits: list[CommitRecord], now: datetime) -> int:
    """Return the active time span in days."""

    if not commits:
        return 0
    return max(days_between(commits[0].committed_at, commits[-1].committed_at), 1)


def group_commits(commits: list[CommitRecord], granularity: str) -> ChartVariant:
    """Group commits by day, week, or month."""

    labels: list[str] = []
    counts: dict[str, int] = defaultdict(int)
    additions: dict[str, int] = defaultdict(int)
    deletions: dict[str, int] = defaultdict(int)

    for commit in commits:
        if granularity == "day":
            label = commit.committed_at.strftime("%Y-%m-%d")
        elif granularity == "week":
            iso_year, iso_week, _ = commit.committed_at.isocalendar()
            label = f"{iso_year}-W{iso_week:02d}"
        else:
            label = commit.committed_at.strftime("%Y-%m")
        counts[label] += 1
        additions[label] += commit.additions
        deletions[label] += commit.deletions

    labels = sorted(counts)
    return ChartVariant(
        labels=labels,
        y_label="Commits",
        series=[
            ChartSeries(name="Commits", values=[counts[label] for label in labels], color="#2563eb"),
            ChartSeries(name="Additions", values=[additions[label] for label in labels], color="#16a34a"),
            ChartSeries(name="Deletions", values=[deletions[label] for label in labels], color="#dc2626"),
        ],
    )


def build_commit_trend_variants(commits: list[CommitRecord]) -> dict[str, ChartVariant]:
    """Prepare day/week/month variants for reusable trend charts."""

    return {
        "day": group_commits(commits, "day"),
        "week": group_commits(commits, "week"),
        "month": group_commits(commits, "month"),
    }


def build_heatmap(commits: list[CommitRecord]) -> list[HeatmapCell]:
    """Build weekday x week heatmap cells."""

    cells: dict[tuple[str, str], int] = defaultdict(int)
    for commit in commits:
        iso_year, iso_week, iso_weekday = commit.committed_at.isocalendar()
        week = f"{iso_year}-W{iso_week:02d}"
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][iso_weekday - 1]
        cells[(week, weekday)] += 1

    heatmap: list[HeatmapCell] = []
    for (week, weekday), value in sorted(cells.items()):
        heatmap.append(HeatmapCell(week=week, weekday=weekday, value=value, tooltip=f"{week} {weekday}: {value} commits"))
    return heatmap


def commit_size_buckets(commits: list[CommitRecord]) -> ChartVariant:
    """Bucket commits by changed line count."""

    buckets = {
        "0-9": 0,
        "10-49": 0,
        "50-99": 0,
        "100-249": 0,
        "250+": 0,
    }
    for commit in commits:
        size = commit.additions + commit.deletions
        if size < 10:
            buckets["0-9"] += 1
        elif size < 50:
            buckets["10-49"] += 1
        elif size < 100:
            buckets["50-99"] += 1
        elif size < 250:
            buckets["100-249"] += 1
        else:
            buckets["250+"] += 1
    labels = list(buckets)
    return ChartVariant(
        labels=labels,
        y_label="Commits",
        series=[ChartSeries(name="Commit count", values=[buckets[label] for label in labels], color="#7c3aed")],
    )


def summarize_peak_period(commits: list[CommitRecord], granularity: str) -> tuple[str, int]:
    """Return the busiest period label for a given granularity."""

    variant = group_commits(commits, granularity)
    if not variant.labels:
        return ("N/A", 0)
    indexed = list(zip(variant.labels, variant.series[0].values, strict=True))
    label, value = max(indexed, key=lambda item: item[1])
    return (label, int(value))


def humanized_age_label(start: datetime | None, end: datetime | None) -> str:
    """Render a compact age label."""

    if start is None or end is None:
        return "N/A"
    days = days_between(start, end)
    if days < 30:
        return f"{days} days"
    if days < 365:
        return f"{ceil(days / 30)} months"
    return f"{ceil(days / 365)} years"


def iso_or_dash(value: datetime | None) -> str:
    """Format datetimes consistently for tables."""

    return format_iso(value) or "-"
