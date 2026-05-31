from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from gitscope.cli.app import app

runner = CliRunner()


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return completed.stdout


def commit_env(timestamp: str) -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = timestamp
    env["GIT_COMMITTER_DATE"] = timestamp
    return env


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Alice")
    git(repo, "config", "user.email", "alice@example.com")

    write_file(repo / "README.md", "# Sample\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Initial commit", env=commit_env("2025-01-01T09:00:00+00:00"))

    git(repo, "checkout", "-b", "feature/demo")
    write_file(repo / "feature.txt", "feature work\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Add feature work", env=commit_env("2025-01-02T10:00:00+00:00"))

    git(repo, "checkout", "main")
    write_file(repo / "README.md", "# Sample\n\nupdated\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Update readme", env=commit_env("2025-01-03T11:00:00+00:00"))
    git(repo, "tag", "v0.1.0")
    return repo


def read_report(path: Path) -> dict:
    return json.loads((path / "report.json").read_text(encoding="utf-8"))


def section(report: dict, section_id: str) -> dict:
    return next(item for item in report["sections"] if item["id"] == section_id)


def metric_value(report: dict, section_id: str, metric_id: str) -> str:
    metrics = section(report, section_id)["summary"]
    return next(item["value"] for item in metrics if item["id"] == metric_id)


def test_analyze_generates_static_report(tmp_path: Path) -> None:
    repo = build_sample_repo(tmp_path)
    output_dir = tmp_path / "report"

    result = runner.invoke(app, ["analyze", str(repo), "--output", str(output_dir)])

    assert result.exit_code == 0, result.stdout
    assert (output_dir / "index.html").exists()
    assert (output_dir / "report.json").exists()
    assert (output_dir / "assets" / "report.css").exists()
    assert (output_dir / "assets" / "report.js").exists()

    report = read_report(output_dir)
    assert report["metadata"]["repository_name"] == "sample-repo"
    assert [item["id"] for item in report["sections"]] == [
        "overview",
        "commits",
        "contributors",
        "branches",
        "files",
        "timeline",
    ]
    assert metric_value(report, "overview", "total-commits") == "3"
    branch_rows = section(report, "branches")["tables"][0]["rows"]
    feature_row = next(row for row in branch_rows if row["name"] == "feature/demo")
    assert "AHEAD" in feature_row["status"]
    assert "BEHIND" in feature_row["status"]


def test_branch_filter_limits_commit_scope(tmp_path: Path) -> None:
    repo = build_sample_repo(tmp_path)
    output_dir = tmp_path / "main-only-report"

    result = runner.invoke(app, ["analyze", str(repo), "--output", str(output_dir), "--branch", "main"])

    assert result.exit_code == 0, result.stdout
    report = read_report(output_dir)
    assert report["metadata"]["filters"]["branch"] == "main"
    assert metric_value(report, "commits", "commit-total") == "2"


def test_invalid_time_range_returns_error(tmp_path: Path) -> None:
    repo = build_sample_repo(tmp_path)
    output_dir = tmp_path / "broken-report"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(repo),
            "--output",
            str(output_dir),
            "--since",
            "2025-02-01",
            "--until",
            "2025-01-01",
        ],
    )

    assert result.exit_code == 1
    assert "must be earlier than or equal to" in result.stderr
