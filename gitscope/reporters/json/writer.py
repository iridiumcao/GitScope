"""Write the report document to report.json."""

from __future__ import annotations

import json
from pathlib import Path

from gitscope.core.models.report import ReportDocument


class JSONReportWriter:
    """Persist the unified report document as JSON."""

    def write(self, output_dir: Path, report: ReportDocument) -> Path:
        json_path = output_dir / "report.json"
        json_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return json_path
