"""Repository collector orchestration."""

from __future__ import annotations

from gitscope.core.git.client import GitClient
from gitscope.core.models.domain import AnalysisRequest, FileRecord, RepositoryMetadata, RepositorySnapshot
from gitscope.core.utils.strings import file_extension


class RepositoryCollector:
    """Collect all raw Git data needed for analysis."""

    def collect(self, request: AnalysisRequest) -> RepositorySnapshot:
        """Collect repository metadata, commits, branches, files, and tags."""

        client = GitClient(request.repo_path)
        repo_root = client.validate_repository()
        current_branch = client.current_branch()
        if request.branch:
            client.ensure_branch(request.branch)
        default_branch = client.default_branch(current_branch)
        analyzed_ref = request.branch or current_branch or default_branch or "HEAD"

        commits = client.collect_commits(request.branch, request.since, request.until)
        current_files = client.list_current_files(request.branch or "HEAD")
        branches = client.list_branches(current_branch=current_branch, default_branch=default_branch)
        tags = client.list_tags()

        repository = RepositoryMetadata(
            name=repo_root.name,
            path=str(repo_root),
            current_branch=current_branch,
            default_branch=default_branch,
            analyzed_ref=analyzed_ref,
            first_commit_at=commits[0].committed_at if commits else None,
            last_commit_at=commits[-1].committed_at if commits else None,
            total_files=len(current_files),
        )
        files = self._aggregate_files(commits, current_files)
        return RepositorySnapshot(
            repository=repository,
            commits=commits,
            branches=branches,
            files=files,
            tags=tags,
        )

    def _aggregate_files(self, commits, current_files: list[str]) -> list[FileRecord]:
        """Build file activity summaries from commit-level file changes."""

        file_stats: dict[str, FileRecord] = {}
        current_file_set = set(current_files)

        for commit in commits:
            for change in commit.files:
                entry = file_stats.get(change.path)
                if entry is None:
                    entry = FileRecord(
                        path=change.path,
                        extension=file_extension(change.path),
                        first_seen_at=commit.committed_at,
                        last_seen_at=commit.committed_at,
                        current_exists=change.path in current_file_set,
                    )
                    file_stats[change.path] = entry
                entry.first_seen_at = min(
                    filter(None, [entry.first_seen_at, commit.committed_at]),
                    default=commit.committed_at,
                )
                entry.last_seen_at = max(
                    filter(None, [entry.last_seen_at, commit.committed_at]),
                    default=commit.committed_at,
                )
                entry.additions += change.additions
                entry.deletions += change.deletions
                entry.change_count += 1

        for path in current_files:
            file_stats.setdefault(
                path,
                FileRecord(
                    path=path,
                    extension=file_extension(path),
                    current_exists=True,
                ),
            )

        files = list(file_stats.values())
        files.sort(key=lambda item: item.path)
        return files
