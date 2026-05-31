"""Low-level Git command access."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from gitscope.core.git.errors import GitCommandError, ValidationError
from gitscope.core.models.domain import BranchRecord, CommitFileChange, CommitRecord, TagRecord
from gitscope.core.utils.time import to_naive_utc


class GitClient:
    """Thin wrapper around the local Git CLI."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path.resolve()

    def run(self, *args: str, check: bool = True) -> str:
        """Execute a Git command in the repository."""

        command = ["git", "-C", str(self.repo_path), "--no-pager", *args]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if check and completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "Git command failed."
            raise GitCommandError(message)
        return completed.stdout

    def validate_repository(self) -> Path:
        """Resolve and validate the repository path."""

        if not self.repo_path.exists():
            raise ValidationError(f"Repository path does not exist: {self.repo_path}")
        if not self.repo_path.is_dir():
            raise ValidationError(f"Repository path is not a directory: {self.repo_path}")

        try:
            root = self.run("rev-parse", "--show-toplevel").strip()
        except GitCommandError as exc:
            raise ValidationError(f"Not a Git repository: {self.repo_path}") from exc
        return Path(root)

    def has_commits(self) -> bool:
        """Return whether HEAD resolves to a commit."""

        completed = subprocess.run(
            ["git", "-C", str(self.repo_path), "--no-pager", "rev-parse", "--verify", "HEAD^{commit}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return completed.returncode == 0

    def ref_exists(self, ref_name: str) -> bool:
        """Check whether a ref resolves to a commit."""

        completed = subprocess.run(
            ["git", "-C", str(self.repo_path), "--no-pager", "rev-parse", "--verify", f"{ref_name}^{{commit}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return completed.returncode == 0

    def current_branch(self) -> str | None:
        """Return the currently checked-out branch if available."""

        output = self.run("branch", "--show-current", check=False).strip()
        return output or None

    def default_branch(self, current_branch: str | None = None) -> str | None:
        """Best-effort default branch detection."""

        remote_head = self.run("symbolic-ref", "refs/remotes/origin/HEAD", "--short", check=False).strip()
        if remote_head.startswith("origin/"):
            return remote_head.removeprefix("origin/")
        for candidate in ("main", "master"):
            if self.ref_exists(candidate):
                return candidate
        return current_branch

    def ensure_branch(self, branch: str) -> None:
        """Validate that a branch-like ref exists."""

        if self.ref_exists(branch):
            return
        if self.ref_exists(f"refs/heads/{branch}"):
            return
        if self.ref_exists(f"refs/remotes/{branch}"):
            return
        raise ValidationError(f"Branch does not exist: {branch}")

    def list_current_files(self, ref_name: str) -> list[str]:
        """List files present at the analyzed ref."""

        if not self.ref_exists(ref_name):
            return []
        output = self.run("ls-tree", "-r", "--name-only", ref_name)
        return [line for line in output.splitlines() if line.strip()]

    def list_tags(self) -> list[TagRecord]:
        """List repository tags."""

        output = self.run(
            "tag",
            "--list",
            "--format=%(refname:short)\t%(objectname)\t%(creatordate:iso-strict)",
            check=False,
        )
        tags: list[TagRecord] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            name, target_sha, created_at_raw = (line.split("\t") + ["", ""])[:3]
            created_at = None
            if created_at_raw:
                created_at = to_naive_utc(datetime.fromisoformat(created_at_raw.replace("Z", "+00:00")))
            tags.append(TagRecord(name=name, target_sha=target_sha or None, created_at=created_at))
        return tags

    def list_branches(self, current_branch: str | None, default_branch: str | None) -> list[BranchRecord]:
        """List local and remote branches with ahead/behind status."""

        outputs = [
            (
                self.run(
                    "for-each-ref",
                    "--format=%(refname)\t%(refname:short)\t%(objectname)\t%(committerdate:iso-strict)",
                    "refs/heads/",
                    check=False,
                ),
                False,
            ),
            (
                self.run(
                    "for-each-ref",
                    "--format=%(refname)\t%(refname:short)\t%(objectname)\t%(committerdate:iso-strict)",
                    "refs/remotes/",
                    check=False,
                ),
                True,
            ),
        ]
        remote_default = f"origin/{default_branch}" if default_branch and self.ref_exists(f"origin/{default_branch}") else default_branch
        branches: list[BranchRecord] = []
        seen: set[str] = set()
        for output, is_remote in outputs:
            for line in output.splitlines():
                if not line.strip():
                    continue
                full_ref, short_name, sha, committed_at_raw = (line.split("\t") + ["", "", "", ""])[:4]
                if not short_name or short_name == "origin/HEAD" or short_name in seen:
                    continue
                seen.add(short_name)
                compare_ref = remote_default if is_remote else default_branch
                ahead_count, behind_count = self._ahead_behind(short_name, compare_ref)
                first_unique_commit_at = self._first_unique_commit(short_name, compare_ref)
                last_commit_at = None
                if committed_at_raw:
                    last_commit_at = to_naive_utc(datetime.fromisoformat(committed_at_raw.replace("Z", "+00:00")))
                branches.append(
                    BranchRecord(
                        name=short_name,
                        is_local=not is_remote,
                        is_remote=is_remote,
                        head_sha=sha or None,
                        last_commit_at=last_commit_at,
                        first_unique_commit_at=first_unique_commit_at,
                        ahead_count=ahead_count,
                        behind_count=behind_count,
                        is_current=bool(current_branch and short_name == current_branch),
                    )
                )
        branches.sort(key=lambda branch: (branch.is_remote, branch.name))
        return branches

    def collect_commits(self, branch: str | None, since: str | None, until: str | None) -> list[CommitRecord]:
        """Collect commit history and numstat data."""

        if not self.has_commits():
            return []

        args = [
            "log",
            "--date=iso-strict",
            "--numstat",
            "--format=%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%P",
        ]
        if since:
            args.append(f"--since={since}")
        if until:
            args.append(f"--until={until}")
        if branch:
            args.append(branch)
        else:
            args.append("--all")

        output = self.run(*args, check=False)
        commits: list[CommitRecord] = []
        for raw_block in output.split("\x1e"):
            block = raw_block.strip()
            if not block:
                continue
            lines = block.splitlines()
            metadata = (lines[0].split("\x1f") + ["", "", "", "", "", ""])[:6]
            sha, author_name, author_email, committed_at_raw, message, parents_raw = metadata
            committed_at = to_naive_utc(datetime.fromisoformat(committed_at_raw.replace("Z", "+00:00")))
            files: list[CommitFileChange] = []
            additions = 0
            deletions = 0
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) < 3:
                    continue
                added_raw, deleted_raw, path = parts[0], parts[1], parts[2]
                added = int(added_raw) if added_raw.isdigit() else 0
                deleted = int(deleted_raw) if deleted_raw.isdigit() else 0
                additions += added
                deletions += deleted
                files.append(CommitFileChange(path=path, additions=added, deletions=deleted))

            commits.append(
                CommitRecord(
                    sha=sha,
                    author_name=author_name,
                    author_email=author_email,
                    committed_at=committed_at,
                    message=message,
                    parents_count=len([parent for parent in parents_raw.split() if parent]),
                    additions=additions,
                    deletions=deletions,
                    changed_files=len(files),
                    branch_hint=branch,
                    files=files,
                )
            )
        commits.sort(key=lambda commit: commit.committed_at)
        return commits

    def _ahead_behind(self, branch_name: str, compare_ref: str | None) -> tuple[int, int]:
        """Return ahead/behind counts relative to a comparison ref."""

        if not compare_ref or branch_name == compare_ref or not self.ref_exists(compare_ref):
            return (0, 0)
        output = self.run("rev-list", "--left-right", "--count", f"{branch_name}...{compare_ref}", check=False).strip()
        if not output:
            return (0, 0)
        ahead_raw, behind_raw = (output.split() + ["0", "0"])[:2]
        return (int(ahead_raw), int(behind_raw))

    def _first_unique_commit(self, branch_name: str, compare_ref: str | None) -> datetime | None:
        """Return the oldest unique commit on a branch compared with the default branch."""

        if not self.ref_exists(branch_name):
            return None
        args = ["log", "--reverse", "--format=%aI", "--max-count=1"]
        if compare_ref and compare_ref != branch_name and self.ref_exists(compare_ref):
            args.append(f"{compare_ref}..{branch_name}")
        else:
            args.append(branch_name)
        output = self.run(*args, check=False).strip()
        if not output:
            return None
        return to_naive_utc(datetime.fromisoformat(output.replace("Z", "+00:00")))
