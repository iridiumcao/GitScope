from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from gitscope.core.analyzers.sections import build_report_payload
from gitscope.core.collectors.repository import RepositoryCollector
from gitscope.core.models.domain import AnalysisFilters
from gitscope.core.utils.errors import InvalidDateRangeError, OutputDirectoryError
from gitscope.reporters.html_reporter import HtmlReporter
from gitscope.reporters.json_reporter import JsonReporter
from gitscope.storage.database import create_session_factory
from gitscope.storage.ingest import ingest_repository


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_path: Path
    output_path: Path
    branch: str | None = None
    since: date | None = None
    until: date | None = None


@dataclass(slots=True)
class AnalysisResult:
    output_path: Path
    report_path: Path
    html_path: Path
    database_path: Path


class AnalysisService:
    """Orchestrate collection, persistence, analysis, and reporting."""

    def run(self, request: AnalysisRequest) -> AnalysisResult:
        if request.since and request.until and request.since > request.until:
            raise InvalidDateRangeError("--since must be earlier than or equal to --until.")

        output_path = request.output_path
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / "assets").mkdir(parents=True, exist_ok=True)
            (output_path / ".gitscope").mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputDirectoryError(f"Cannot write to output directory: {output_path}") from exc

        database_path = output_path / ".gitscope" / "analysis.sqlite3"
        if database_path.exists():
            database_path.unlink()

        filters = AnalysisFilters(
            repo_path=str(request.repo_path),
            branch=request.branch,
            since=request.since,
            until=request.until,
        )
        snapshot = RepositoryCollector(request.repo_path).collect(filters)

        session_factory = create_session_factory(database_path)
        with session_factory() as session:
            ingest_repository(session, snapshot)
            payload = build_report_payload(
                session,
                filters={
                    "branch": request.branch,
                    "since": request.since.isoformat() if request.since else None,
                    "until": request.until.isoformat() if request.until else None,
                },
            )

        report_path = JsonReporter().write(output_path, payload)
        html_path = HtmlReporter().write(output_path, payload)

        return AnalysisResult(
            output_path=output_path,
            report_path=report_path,
            html_path=html_path,
            database_path=database_path,
        )
