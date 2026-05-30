from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from gitscope.core.models.domain import CollectedRepository
from gitscope.storage.schema import BranchRecord, CommitFileRecord, CommitRecord, ContributorRecord, FileRecord, RepositoryRecord, TagRecord


def ingest_repository(session: Session, snapshot: CollectedRepository) -> None:
    now = datetime.now(UTC)
    repository = RepositoryRecord(
        name=snapshot.name,
        path=snapshot.path,
        current_branch=snapshot.current_branch,
        default_branch=snapshot.default_branch,
        first_commit_at=snapshot.commits[0].committed_at if snapshot.commits else None,
        last_commit_at=snapshot.commits[-1].committed_at if snapshot.commits else None,
        created_at=now,
        updated_at=now,
    )
    session.add(repository)
    session.flush()

    contributor_ids: dict[str, int] = {}
    for commit in snapshot.commits:
        normalized_key = f"{commit.author_name.lower()}<{commit.author_email.lower()}>"
        if normalized_key in contributor_ids:
            continue
        contributor = ContributorRecord(
            name=commit.author_name,
            email=commit.author_email,
            normalized_key=normalized_key,
        )
        session.add(contributor)
        session.flush()
        contributor_ids[normalized_key] = contributor.id

    file_rows: dict[str, FileRecord] = {}
    for path in snapshot.files:
        record = FileRecord(
            repository_id=repository.id,
            path=path,
            extension=Path(path).suffix.lstrip("."),
            first_seen_at=None,
            last_seen_at=None,
        )
        session.add(record)
        session.flush()
        file_rows[path] = record

    for tag in snapshot.tags:
        session.add(TagRecord(repository_id=repository.id, name=tag))

    for branch in snapshot.branches:
        session.add(
            BranchRecord(
                repository_id=repository.id,
                name=branch.name,
                is_local=branch.is_local,
                is_remote=branch.is_remote,
                head_sha=branch.head_sha,
                last_commit_at=branch.last_commit_at,
                ahead_count=branch.ahead_count,
                behind_count=branch.behind_count,
            )
        )

    for commit in snapshot.commits:
        normalized_key = f"{commit.author_name.lower()}<{commit.author_email.lower()}>"
        commit_row = CommitRecord(
            sha=commit.sha,
            repository_id=repository.id,
            author_id=contributor_ids[normalized_key],
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

        for file_change in commit.files:
            file_row = file_rows.get(file_change.path)
            if file_row is None:
                file_row = FileRecord(
                    repository_id=repository.id,
                    path=file_change.path,
                    extension=Path(file_change.path).suffix.lstrip("."),
                    first_seen_at=commit.committed_at,
                    last_seen_at=commit.committed_at,
                )
                session.add(file_row)
                session.flush()
                file_rows[file_change.path] = file_row

            if file_row.first_seen_at is None or commit.committed_at < file_row.first_seen_at:
                file_row.first_seen_at = commit.committed_at
            if file_row.last_seen_at is None or commit.committed_at > file_row.last_seen_at:
                file_row.last_seen_at = commit.committed_at

            session.add(
                CommitFileRecord(
                    commit_sha=commit.sha,
                    file_id=file_row.id,
                    change_type=file_change.change_type,
                    additions=file_change.additions,
                    deletions=file_change.deletions,
                )
            )

    session.commit()
