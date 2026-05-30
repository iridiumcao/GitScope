from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "--no-pager", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.name", "Alice")
    run_git(repo, "config", "user.email", "alice@example.com")

    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "Add README")

    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    run_git(repo, "add", "app.py")
    run_git(repo, "commit", "-m", "Add app")

    run_git(repo, "checkout", "-b", "feature/docs")
    run_git(repo, "config", "user.name", "Bob")
    run_git(repo, "config", "user.email", "bob@example.com")
    (repo / "README.md").write_text("# Demo\n\nUpdated\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "Update docs")
    run_git(repo, "checkout", "main")

    run_git(repo, "tag", "v0.1.0")
    return repo
