from __future__ import annotations

import subprocess
from pathlib import Path

from gitscope.core.utils.errors import GitCommandError


class GitClient:
    """Small wrapper around the local git executable."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path

    def run(self, *args: str, allow_failure: bool = False) -> str:
        command = ["git", "--no-pager", *args]
        completed = subprocess.run(
            command,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0 and not allow_failure:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "Unknown git error."
            raise GitCommandError(f"Git command failed: {' '.join(command)}\n{stderr}")
        return completed.stdout
