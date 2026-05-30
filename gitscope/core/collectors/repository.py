from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gitscope.core.git.client import GitClient
from gitscope.core.models.domain import (
    AnalysisFilters,
    CollectedBranch,
    CollectedCommit,
    CollectedFileChange,
    CollectedRepository,
)
from gitscope.core.utils.errors import GitCommandError, InvalidBranchError, InvalidRepositoryError

COMMIT_MARKER = "__GITSCOPE_COMMIT__"


class RepositoryCollector:
    """Collect repository state with local Git commands."""

    def __init__(self, repo_path: Path) -> None:
        self.client = GitClient(repo_path)
        self.repo_path = repo_path

    def collect(self, filters: AnalysisFilters) -> CollectedRepository:
        try:
            root = Path(self.client.run("rev-parse", "--show-toplevel").strip())
            is_git_repo = self.client.run("rev-parse", "--is-inside-work-tree").strip()
        except GitCommandError as exc:
            raise InvalidRepositoryError(f"{self.repo_path} is not a Git repository.") from exc
        if is_git_repo != "true":
            raise InvalidRepositoryError(f"{self.repo_path} is not a Git repository.")

        current_branch = self.client.run("rev-parse", "--abbrev-ref", "HEAD").strip()
        default_branch = self._resolve_default_branch(current_branch)

        if filters.branch:
            try:
                self.client.run("rev-parse", "--verify", filters.branch)
            except GitCommandError as exc:
                raise InvalidBranchError(f"Branch '{filters.branch}' does not exist.") from exc

        commits = self._collect_commits(filters)
        branches = self._collect_branches(default_branch=default_branch, current_branch=current_branch)
        tags = [line.strip() for line in self.client.run("tag", "--list").splitlines() if line.strip()]
        tree_ref = filters.branch or current_branch
        files = [line.strip() for line in self.client.run("ls-tree", "-r", "--name-only", tree_ref).splitlines() if line.strip()]

        return CollectedRepository(
            name=root.name,
            path=str(root),
            current_branch=current_branch,
            default_branch=default_branch,
            tags=tags,
            files=files,
            commits=commits,
            branches=branches,
        )

    def _resolve_default_branch(self, current_branch: str) -> str:
        remote_head = self.client.run("symbolic-ref", "refs/remotes/origin/HEAD", allow_failure=True).strip()
        if remote_head:
            return remote_head.rsplit("/", maxsplit=1)[-1]

        branch_names = {
            line.strip()
            for line in self.client.run("for-each-ref", "refs/heads", "--format=%(refname:short)").splitlines()
            if line.strip()
        }
        for candidate in ("main", "master"):
            if candidate in branch_names:
                return candidate
        return current_branch

    def _collect_commits(self, filters: AnalysisFilters) -> list[CollectedCommit]:
        args = [
            "log",
            "--date=iso-strict",
            "--numstat",
            f"--format={COMMIT_MARKER}%n%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%P",
        ]
        if filters.since:
            args.append(f"--since={filters.since.isoformat()}")
        if filters.until:
            args.append(f"--until={filters.until.isoformat()}T23:59:59")
        args.append(filters.branch or "--all")

        output = self.client.run(*args)
        commits: list[CollectedCommit] = []
        metadata: list[str] | None = None
        files: list[CollectedFileChange] = []

        def finalize() -> None:
            nonlocal metadata, files
            if metadata is None:
                return
            sha, author_name, author_email, committed_at, message, parents = metadata
            commits.append(
                CollectedCommit(
                    sha=sha,
                    author_name=author_name,
                    author_email=author_email,
                    committed_at=datetime.fromisoformat(committed_at),
                    message=message,
                    parents_count=len(parents.split()) if parents else 0,
                    additions=sum(item.additions for item in files),
                    deletions=sum(item.deletions for item in files),
                    changed_files=len(files),
                    branch_hint=filters.branch,
                    files=files,
                )
            )
            metadata = None
            files = []

        for line in output.splitlines():
            if line == COMMIT_MARKER:
                finalize()
                metadata = None
                files = []
                continue

            if metadata is None:
                if not line.strip():
                    continue
                metadata = line.split("\x1f")
                continue

            if not line.strip():
                continue

            parts = line.split("\t", maxsplit=2)
            if len(parts) != 3:
                continue
            additions_raw, deletions_raw, path = parts
            files.append(
                CollectedFileChange(
                    path=path,
                    change_type=self._infer_change_type(additions_raw, deletions_raw),
                    additions=int(additions_raw) if additions_raw.isdigit() else 0,
                    deletions=int(deletions_raw) if deletions_raw.isdigit() else 0,
                )
            )

        finalize()
        commits.sort(key=lambda item: item.committed_at)
        return commits

    def _collect_branches(self, default_branch: str, current_branch: str) -> list[CollectedBranch]:
        rows = self.client.run(
            "for-each-ref",
            "refs/heads",
            "refs/remotes",
            "--format=%(refname:short)%x1f%(refname)%x1f%(objectname)%x1f%(committerdate:iso-strict)",
        )
        refs: dict[str, tuple[str, str, str, str]] = {}
        for line in rows.splitlines():
            if not line.strip():
                continue
            short_name, full_name, head_sha, committed_at = line.split("\x1f")
            if short_name.endswith("/HEAD"):
                continue
            refs[short_name] = (short_name, full_name, head_sha, committed_at)

        branches: list[CollectedBranch] = []
        default_remote = f"origin/{default_branch}"
        for short_name, full_name, head_sha, committed_at in refs.values():
            is_local = full_name.startswith("refs/heads/")
            is_remote = full_name.startswith("refs/remotes/")
            base_ref: str | None = None
            if is_remote and default_remote in refs:
                base_ref = default_remote
            elif default_branch in refs:
                base_ref = default_branch
            elif current_branch in refs:
                base_ref = current_branch

            ahead_count = 0
            behind_count = 0
            if base_ref and base_ref != short_name:
                counts = self.client.run("rev-list", "--left-right", "--count", f"{short_name}...{base_ref}", allow_failure=True).strip()
                if counts:
                    ahead_raw, behind_raw = counts.split()
                    ahead_count = int(ahead_raw)
                    behind_count = int(behind_raw)

            branches.append(
                CollectedBranch(
                    name=short_name,
                    is_local=is_local,
                    is_remote=is_remote,
                    head_sha=head_sha,
                    last_commit_at=datetime.fromisoformat(committed_at) if committed_at else None,
                    ahead_count=ahead_count,
                    behind_count=behind_count,
                )
            )

        branches.sort(key=lambda item: item.name.lower())
        return branches

    @staticmethod
    def _infer_change_type(additions_raw: str, deletions_raw: str) -> str:
        if additions_raw == "0" and deletions_raw.isdigit() and int(deletions_raw) > 0:
            return "deleted"
        if deletions_raw == "0" and additions_raw.isdigit() and int(additions_raw) > 0:
            return "added"
        return "modified"
