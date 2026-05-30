from __future__ import annotations

import json
from pathlib import Path

from gitscope.core.services.analysis import AnalysisRequest, AnalysisService


def test_branch_filter_limits_commit_scope(sample_repo: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "report"

    result = AnalysisService().run(
        AnalysisRequest(
            repo_path=sample_repo,
            output_path=output_path,
            branch="main",
        )
    )

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["metadata"]["branch"] == "main"
    assert report["pages"]["overview"]["summary"]["total_commits"] == 2
