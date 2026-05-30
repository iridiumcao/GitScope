from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class AnalysisFilters(BaseModel):
    repo_path: str
    branch: str | None = None
    since: date | None = None
    until: date | None = None


class CollectedFileChange(BaseModel):
    path: str
    change_type: str
    additions: int = 0
    deletions: int = 0


class CollectedCommit(BaseModel):
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
    files: list[CollectedFileChange] = Field(default_factory=list)


class CollectedBranch(BaseModel):
    name: str
    is_local: bool
    is_remote: bool
    head_sha: str
    last_commit_at: datetime | None = None
    ahead_count: int = 0
    behind_count: int = 0


class CollectedRepository(BaseModel):
    name: str
    path: str
    current_branch: str
    default_branch: str
    tags: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    commits: list[CollectedCommit] = Field(default_factory=list)
    branches: list[CollectedBranch] = Field(default_factory=list)
