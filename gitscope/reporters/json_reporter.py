from __future__ import annotations

from pathlib import Path

from gitscope.core.models.report import ReportPayload


class JsonReporter:
    def write(self, output_path: Path, payload: ReportPayload) -> Path:
        target = output_path / "report.json"
        target.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
        return target
