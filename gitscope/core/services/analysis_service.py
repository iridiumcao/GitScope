"""End-to-end analysis service."""

from __future__ import annotations

from pathlib import Path

from gitscope.core.collectors.repository import RepositoryCollector
from gitscope.core.git.errors import ValidationError
from gitscope.core.models.domain import AnalysisRequest, AnalysisResult
from gitscope.core.services.report_builder import ReportBuilder
from gitscope.core.utils.time import parse_since, parse_until
from gitscope.reporters.html.writer import HTMLReportWriter
from gitscope.reporters.json.writer import JSONReportWriter
from gitscope.storage.store import SQLiteStore


class AnalysisService:
    """Coordinate collection, persistence, analysis, and reporting."""

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Run the full analysis pipeline."""

        since = parse_since(request.since)
        until = parse_until(request.until)
        if since and until and since > until:
            raise ValidationError("The --since value must be earlier than or equal to --until.")

        output_dir = self._prepare_output_dir(request.output_path)
        normalized_request = request.model_copy(update={"repo_path": request.repo_path.resolve(), "output_path": output_dir})

        snapshot = RepositoryCollector().collect(normalized_request)
        store = SQLiteStore()
        store.ingest(snapshot)
        context = store.load_context(normalized_request)
        report = ReportBuilder().build(context)

        json_writer = JSONReportWriter()
        html_writer = HTMLReportWriter()
        json_path = json_writer.write(output_dir, report)
        index_path = html_writer.write(output_dir, report)

        return AnalysisResult(output_dir=output_dir, json_path=json_path, index_path=index_path)

    def _prepare_output_dir(self, output_path: Path) -> Path:
        """Validate and create the output directory."""

        resolved = output_path.resolve()
        if resolved.exists() and not resolved.is_dir():
            raise ValidationError(f"Output path must be a directory: {resolved}")
        try:
            resolved.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValidationError(f"Unable to create output directory: {resolved}") from exc
        return resolved
