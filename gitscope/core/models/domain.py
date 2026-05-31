"""Domain models shared by collectors, storage, analyzers, and reporters."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Validated CLI input for a single analysis run."""

    repo_path: Path
    output_path: Path
    branch: str | None = None
    since: str | None = None
    until: str | None = None


class CommitFileChange(BaseModel):
    """A file touched by a commit."""

    path: str
    additions: int = 0
    deletions: int = 0
    change_type: str = "modified"


class CommitRecord(BaseModel):
    """Normalized commit data collected from Git."""

    sha: str
    author_name: str
    author_email: str
    committed_at: datetime
    message: str
    parents_count: int
    additions: int
    deletions: int
    changed_files: int
    branch_hint: str | None = None
    files: list[CommitFileChange] = Field(default_factory=list)


class BranchRecord(BaseModel):
    """Branch metadata derived from refs and comparison against the default branch."""

    name: str
    is_local: bool
    is_remote: bool
    head_sha: str | None = None
    last_commit_at: datetime | None = None
    first_unique_commit_at: datetime | None = None
    ahead_count: int = 0
    behind_count: int = 0
    is_current: bool = False


class FileRecord(BaseModel):
    """Normalized file-level activity summary."""

    path: str
    extension: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    additions: int = 0
    deletions: int = 0
    change_count: int = 0
    current_exists: bool = True


class TagRecord(BaseModel):
    """Git tag metadata."""

    name: str
    target_sha: str | None = None
    created_at: datetime | None = None


class ContributorRecord(BaseModel):
    """Contributor summary persisted in SQLite."""

    name: str
    email: str
    normalized_key: str
    commit_count: int = 0
    additions: int = 0
    deletions: int = 0
    last_commit_at: datetime | None = None


class RepositoryMetadata(BaseModel):
    """Repository-level metadata captured before analysis."""

    name: str
    path: str
    current_branch: str | None = None
    default_branch: str | None = None
    analyzed_ref: str
    first_commit_at: datetime | None = None
    last_commit_at: datetime | None = None
    total_files: int = 0


class RepositorySnapshot(BaseModel):
    """Collector output before it is written to SQLite."""

    repository: RepositoryMetadata
    commits: list[CommitRecord] = Field(default_factory=list)
    branches: list[BranchRecord] = Field(default_factory=list)
    files: list[FileRecord] = Field(default_factory=list)
    tags: list[TagRecord] = Field(default_factory=list)


class AnalysisContext(BaseModel):
    """Data loaded back from SQLite for analyzer use."""

    request: AnalysisRequest
    repository: RepositoryMetadata
    commits: list[CommitRecord] = Field(default_factory=list)
    contributors: list[ContributorRecord] = Field(default_factory=list)
    branches: list[BranchRecord] = Field(default_factory=list)
    files: list[FileRecord] = Field(default_factory=list)
    tags: list[TagRecord] = Field(default_factory=list)
    generated_at: datetime


class AnalysisResult(BaseModel):
    """Paths returned after report generation completes."""

    output_dir: Path
    json_path: Path
    index_path: Path
