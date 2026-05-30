from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SummaryCard(BaseModel):
    label: str
    value: str
    hint: str | None = None


class ChartSeries(BaseModel):
    name: str
    values: list[float | int] = Field(default_factory=list)


class HeatmapCell(BaseModel):
    date: str
    week: int
    weekday: int
    value: int


class ChartSpec(BaseModel):
    type: str
    title: str
    description: str
    labels: list[str] = Field(default_factory=list)
    series: list[ChartSeries] = Field(default_factory=list)
    cells: list[HeatmapCell] = Field(default_factory=list)


class TableSpec(BaseModel):
    title: str
    columns: list[str]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    empty_message: str = "No data available."


class ReportSection(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    cards: list[SummaryCard] = Field(default_factory=list)
    charts: list[ChartSpec] = Field(default_factory=list)
    tables: list[TableSpec] = Field(default_factory=list)
    sections: list["ReportSection"] = Field(default_factory=list)
    empty_state: str | None = None


class ReportPayload(BaseModel):
    metadata: dict[str, Any]
    page_order: list[str]
    pages: dict[str, ReportSection]
