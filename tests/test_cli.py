from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from gitscope.cli.app import app


def test_analyze_generates_report(sample_repo: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "report"
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", str(sample_repo), "--output", str(output_path)])

    assert result.exit_code == 0, result.output
    assert (output_path / "index.html").exists()
    assert (output_path / "report.json").exists()
    assert (output_path / "assets" / "style.css").exists()
    assert (output_path / ".gitscope" / "analysis.sqlite3").exists()

    report = json.loads((output_path / "report.json").read_text(encoding="utf-8"))
    assert report["metadata"]["repository_name"] == "sample-repo"
    assert report["pages"]["overview"]["summary"]["total_commits"] == 3
    assert report["pages"]["branches"]["summary"]["total_branches"] >= 2


def test_analyze_rejects_missing_branch(sample_repo: Path, tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["analyze", str(sample_repo), "--output", str(tmp_path / "report"), "--branch", "missing-branch"],
    )

    assert result.exit_code == 1
    assert "missing-branch" in result.output
