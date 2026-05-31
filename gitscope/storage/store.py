"""Persistence and load-back helpers for the analysis pipeline."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select

from gitscope.core.models.domain import (
    AnalysisContext,
    AnalysisRequest,
    BranchRecord,
    CommitFileChange,
    CommitRecord,
    ContributorRecord,
    FileRecord,
    RepositoryMetadata,
    RepositorySnapshot,
    TagRecord,
)
from gitscope.core.utils.strings import contributor_key
from gitscope.storage.database import SQLiteStoreEngine
from gitscope.storage.schema import BranchORM, CommitFileORM, CommitORM, ContributorORM, FileORM, RepositoryORM, TagORM


class SQLiteStore:
    """Write collector output into SQLite and load it back for analyzers."""

    def __init__(self) -> None:
        self.database = SQLiteStoreEngine()

    def ingest(self, snapshot: RepositorySnapshot) -> None:
        """Persist collector output."""

        with self.database.session() as session:
            repository = RepositoryORM(
                name=snapshot.repository.name,
                path=snapshot.repository.path,
                current_branch=snapshot.repository.current_branch,
                default_branch=snapshot.repository.default_branch,
                analyzed_ref=snapshot.repository.analyzed_ref,
                first_commit_at=snapshot.repository.first_commit_at,
                last_commit_at=snapshot.repository.last_commit_at,
                total_files=snapshot.repository.total_files,
            )
            session.add(repository)
            session.flush()

            contributor_map: dict[str, ContributorORM] = {}
            contributor_totals: dict[str, ContributorRecord] = {}
            for commit in snapshot.commits:
                key = contributor_key(commit.author_name, commit.author_email)
                contributor_map.setdefault(
                    key,
                    ContributorORM(
                        repository_id=repository.id,
                        name=commit.author_name,
                        email=commit.author_email,
                        normalized_key=key,
                    ),
                )
                total = contributor_totals.setdefault(
                    key,
                    ContributorRecord(name=commit.author_name, email=commit.author_email, normalized_key=key),
                )
                total.commit_count += 1
                total.additions += commit.additions
                total.deletions += commit.deletions
                if total.last_commit_at is None or commit.committed_at > total.last_commit_at:
                    total.last_commit_at = commit.committed_at

            for key, contributor in contributor_map.items():
                totals = contributor_totals[key]
                contributor.commit_count = totals.commit_count
                contributor.additions = totals.additions
                contributor.deletions = totals.deletions
                contributor.last_commit_at = totals.last_commit_at
                session.add(contributor)
            session.flush()

            file_map: dict[str, FileORM] = {}
            for file_record in snapshot.files:
                file_row = FileORM(
                    repository_id=repository.id,
                    path=file_record.path,
                    extension=file_record.extension,
                    first_seen_at=file_record.first_seen_at,
                    last_seen_at=file_record.last_seen_at,
                    additions=file_record.additions,
                    deletions=file_record.deletions,
                    change_count=file_record.change_count,
                    current_exists=file_record.current_exists,
                )
                session.add(file_row)
                file_map[file_record.path] = file_row
            session.flush()

            for commit in snapshot.commits:
                key = contributor_key(commit.author_name, commit.author_email)
                contributor = contributor_map[key]
                commit_row = CommitORM(
                    sha=commit.sha,
                    repository_id=repository.id,
                    contributor_id=contributor.id,
                    author_name=commit.author_name,
                    author_email=commit.author_email,
                    committed_at=commit.committed_at,
                    message=commit.message,
                    parents_count=commit.parents_count,
                    additions=commit.additions,
                    deletions=commit.deletions,
                    changed_files=commit.changed_files,
                    branch_hint=commit.branch_hint,
                )
                session.add(commit_row)
                session.flush()
                for change in commit.files:
                    file_row = file_map.get(change.path)
                    if file_row is None:
                        continue
                    session.add(
                        CommitFileORM(
                            commit_sha=commit.sha,
                            file_id=file_row.id,
                            additions=change.additions,
                            deletions=change.deletions,
                            change_type=change.change_type,
                        )
                    )

            for branch in snapshot.branches:
                session.add(
                    BranchORM(
                        repository_id=repository.id,
                        name=branch.name,
                        is_local=branch.is_local,
                        is_remote=branch.is_remote,
                        head_sha=branch.head_sha,
                        last_commit_at=branch.last_commit_at,
                        first_unique_commit_at=branch.first_unique_commit_at,
                        ahead_count=branch.ahead_count,
                        behind_count=branch.behind_count,
                        is_current=branch.is_current,
                    )
                )

            for tag in snapshot.tags:
                session.add(
                    TagORM(
                        repository_id=repository.id,
                        name=tag.name,
                        target_sha=tag.target_sha,
                        created_at=tag.created_at,
                    )
                )

            session.commit()

    def load_context(self, request: AnalysisRequest) -> AnalysisContext:
        """Load normalized data back into pydantic models for analyzers."""

        with self.database.session() as session:
            repository_row = session.scalars(select(RepositoryORM)).one()
            contributors = [
                ContributorRecord(
                    name=row.name,
                    email=row.email,
                    normalized_key=row.normalized_key,
                    commit_count=row.commit_count,
                    additions=row.additions,
                    deletions=row.deletions,
                    last_commit_at=row.last_commit_at,
                )
                for row in session.scalars(select(ContributorORM).order_by(ContributorORM.commit_count.desc())).all()
            ]
            commits = [
                CommitRecord(
                    sha=row.sha,
                    author_name=row.author_name,
                    author_email=row.author_email,
                    committed_at=row.committed_at,
                    message=row.message,
                    parents_count=row.parents_count,
                    additions=row.additions,
                    deletions=row.deletions,
                    changed_files=row.changed_files,
                    branch_hint=row.branch_hint,
                    files=[],
                )
                for row in session.scalars(select(CommitORM).order_by(CommitORM.committed_at.asc())).all()
            ]

            file_rows = session.scalars(select(FileORM).order_by(FileORM.path.asc())).all()
            files = [
                FileRecord(
                    path=row.path,
                    extension=row.extension,
                    first_seen_at=row.first_seen_at,
                    last_seen_at=row.last_seen_at,
                    additions=row.additions,
                    deletions=row.deletions,
                    change_count=row.change_count,
                    current_exists=row.current_exists,
                )
                for row in file_rows
            ]

            file_lookup = {row.id: row.path for row in file_rows}
            commit_changes_by_sha: dict[str, list[CommitFileChange]] = defaultdict(list)
            for row in session.scalars(select(CommitFileORM)).all():
                commit_changes_by_sha[row.commit_sha].append(
                    CommitFileChange(
                        path=file_lookup[row.file_id],
                        additions=row.additions,
                        deletions=row.deletions,
                        change_type=row.change_type,
                    )
                )
            for commit in commits:
                commit.files = commit_changes_by_sha.get(commit.sha, [])

            branches = [
                BranchRecord(
                    name=row.name,
                    is_local=row.is_local,
                    is_remote=row.is_remote,
                    head_sha=row.head_sha,
                    last_commit_at=row.last_commit_at,
                    first_unique_commit_at=row.first_unique_commit_at,
                    ahead_count=row.ahead_count,
                    behind_count=row.behind_count,
                    is_current=row.is_current,
                )
                for row in session.scalars(select(BranchORM).order_by(BranchORM.name.asc())).all()
            ]
            tags = [
                TagRecord(name=row.name, target_sha=row.target_sha, created_at=row.created_at)
                for row in session.scalars(select(TagORM).order_by(TagORM.name.asc())).all()
            ]

        return AnalysisContext(
            request=request,
            repository=RepositoryMetadata(
                name=repository_row.name,
                path=repository_row.path,
                current_branch=repository_row.current_branch,
                default_branch=repository_row.default_branch,
                analyzed_ref=repository_row.analyzed_ref,
                first_commit_at=repository_row.first_commit_at,
                last_commit_at=repository_row.last_commit_at,
                total_files=repository_row.total_files,
            ),
            commits=commits,
            contributors=contributors,
            branches=branches,
            files=files,
            tags=tags,
            generated_at=datetime.now(UTC).replace(tzinfo=None),
        )
