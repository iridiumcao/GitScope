"""File analytics."""

from __future__ import annotations

from datetime import datetime

from gitscope.core.analyzers.common import humanized_age_label, metric
from gitscope.core.models.domain import AnalysisContext
from gitscope.core.models.report import ChartData, ChartSeries, ChartVariant, SectionData, TableColumn, TableData


class FileAnalyzer:
    """Build the Files section."""

    def analyze(self, context: AnalysisContext) -> SectionData:
        files = context.files
        now = context.generated_at
        current_files = [file_record for file_record in files if file_record.current_exists]
        changed_files = sorted(files, key=lambda item: (item.change_count, item.last_seen_at or datetime.min), reverse=True)
        added_files = sorted(files, key=lambda item: (item.additions, item.last_seen_at or datetime.min), reverse=True)
        deleted_files = sorted(files, key=lambda item: (item.deletions, item.last_seen_at or datetime.min), reverse=True)
        recently_active = sorted(current_files, key=lambda item: item.last_seen_at or datetime.min, reverse=True)
        inactive = sorted(current_files, key=lambda item: item.last_seen_at or datetime.min)

        summary = [
            metric("files-tracked", "Tracked files", str(len(files)), "Files observed in history or present at the analyzed ref."),
            metric("files-current", "Current files", str(len(current_files)), "Files present at the analyzed ref."),
            metric("files-history-only", "History-only paths", str(len(files) - len(current_files)), "Files seen in history but not in the current tree."),
            metric("files-most-changed", "Most changed file", changed_files[0].path if changed_files else "N/A", "Based on recorded change count."),
        ]

        extension_counts: dict[str, int] = {}
        for file_record in current_files:
            extension = file_record.extension or "[no ext]"
            extension_counts[extension] = extension_counts.get(extension, 0) + 1

        top_extensions = sorted(extension_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        charts = [
            ChartData(
                id="file-extensions",
                title="Current file types",
                description="Top file extensions in the analyzed ref.",
                type="bar",
                default_variant="extensions",
                variants={
                    "extensions": ChartVariant(
                        labels=[label for label, _ in top_extensions],
                        y_label="Files",
                        series=[
                            ChartSeries(
                                name="Files",
                                values=[count for _, count in top_extensions],
                                color="#059669",
                            )
                        ],
                    )
                },
                empty_state="No current files are available yet.",
            )
        ]

        tables = [
            self._build_table(
                "file-most-changed",
                "Most changed files",
                "Files with the highest recorded change count.",
                changed_files[:15],
            ),
            self._build_table(
                "file-most-added",
                "Most added lines",
                "Files ranked by total added lines.",
                added_files[:15],
                sort_key="additions",
            ),
            self._build_table(
                "file-most-deleted",
                "Most deleted lines",
                "Files ranked by total deleted lines.",
                deleted_files[:15],
                sort_key="deletions",
            ),
            TableData(
                id="file-recently-active",
                title="Recently active files",
                description="Current files touched most recently.",
                columns=[
                    TableColumn(key="path", label="File"),
                    TableColumn(key="last_seen_at", label="Last touched"),
                    TableColumn(key="age", label="Last activity age"),
                ],
                rows=[
                    {
                        "path": file_record.path,
                        "last_seen_at": file_record.last_seen_at.isoformat(timespec="seconds") if file_record.last_seen_at else "-",
                        "age": humanized_age_label(file_record.last_seen_at, now),
                    }
                    for file_record in recently_active[:15]
                ],
                empty_state="No current files are available yet.",
            ),
            TableData(
                id="file-inactive",
                title="Inactive files",
                description="Current files with the oldest last activity timestamp.",
                columns=[
                    TableColumn(key="path", label="File"),
                    TableColumn(key="last_seen_at", label="Last touched"),
                    TableColumn(key="age", label="Last activity age"),
                ],
                rows=[
                    {
                        "path": file_record.path,
                        "last_seen_at": file_record.last_seen_at.isoformat(timespec="seconds") if file_record.last_seen_at else "-",
                        "age": humanized_age_label(file_record.last_seen_at, now),
                    }
                    for file_record in inactive[:15]
                ],
                empty_state="No current files are available yet.",
            ),
        ]

        return SectionData(
            id="files",
            title="Files",
            description="File churn, file type distribution, and recent/inactive paths.",
            summary=summary,
            charts=charts,
            tables=tables,
        )

    def _build_table(self, table_id: str, title: str, description: str, file_rows, sort_key: str = "change_count") -> TableData:
        return TableData(
            id=table_id,
            title=title,
            description=description,
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
                for file_record in file_rows
            ],
            empty_state=f"No files are available for {title.lower()}.",
        )
