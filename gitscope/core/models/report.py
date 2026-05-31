"""Unified report schema shared by JSON and HTML reporters."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SummaryMetric(BaseModel):
    """Small metric card shown near the top of a page."""

    id: str
    label: str
    value: str
    hint: str | None = None
    tone: Literal["default", "positive", "warning", "danger"] = "default"


class ChartSeries(BaseModel):
    """Series definition for a chart."""

    name: str
    values: list[int | float]
    color: str | None = None


class ChartVariant(BaseModel):
    """One chart payload variant, such as day/week/month."""

    labels: list[str] = Field(default_factory=list)
    series: list[ChartSeries] = Field(default_factory=list)
    y_label: str | None = None


class HeatmapCell(BaseModel):
    """Single heatmap cell."""

    week: str
    weekday: str
    value: int
    tooltip: str


class ChartData(BaseModel):
    """Chart card payload."""

    id: str
    title: str
    description: str
    type: Literal["line", "bar", "heatmap"]
    default_variant: str | None = None
    variants: dict[str, ChartVariant] = Field(default_factory=dict)
    heatmap: list[HeatmapCell] = Field(default_factory=list)
    empty_state: str | None = None


class TableColumn(BaseModel):
    """Table column descriptor."""

    key: str
    label: str
    align: Literal["left", "right", "center"] = "left"


class TableData(BaseModel):
    """Table card payload."""

    id: str
    title: str
    description: str
    columns: list[TableColumn]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    empty_state: str | None = None


class SectionData(BaseModel):
    """A full report page/section."""

    id: str
    title: str
    description: str
    summary: list[SummaryMetric] = Field(default_factory=list)
    charts: list[ChartData] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReportMetadata(BaseModel):
    """Header metadata shown in the report shell."""

    generated_at: str
    repository_name: str
    repository_path: str
    analyzed_ref: str
    current_branch: str | None = None
    default_branch: str | None = None
    filters: dict[str, str | None]
    warnings: list[str] = Field(default_factory=list)


class ReportDocument(BaseModel):
    """Top-level report document."""

    metadata: ReportMetadata
    summary: list[SummaryMetric] = Field(default_factory=list)
    charts: list[ChartData] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)
    sections: list[SectionData] = Field(default_factory=list)
