"""SQLAlchemy ORM schema for normalized Git data."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for ORM models."""


class RepositoryORM(Base):
    """Single analyzed repository row."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(2048))
    current_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    analyzed_ref: Mapped[str] = mapped_column(String(255))
    first_commit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)

    contributors: Mapped[list["ContributorORM"]] = relationship(back_populates="repository")
    commits: Mapped[list["CommitORM"]] = relationship(back_populates="repository")
    branches: Mapped[list["BranchORM"]] = relationship(back_populates="repository")
    files: Mapped[list["FileORM"]] = relationship(back_populates="repository")
    tags: Mapped[list["TagORM"]] = relationship(back_populates="repository")


class ContributorORM(Base):
    """Contributor summary row."""

    __tablename__ = "contributors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    normalized_key: Mapped[str] = mapped_column(String(512), unique=True)
    commit_count: Mapped[int] = mapped_column(Integer, default=0)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    repository: Mapped[RepositoryORM] = relationship(back_populates="contributors")
    commits: Mapped[list["CommitORM"]] = relationship(back_populates="contributor")


class CommitORM(Base):
    """Commit row."""

    __tablename__ = "commits"

    sha: Mapped[str] = mapped_column(String(64), primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    contributor_id: Mapped[int] = mapped_column(ForeignKey("contributors.id"))
    author_name: Mapped[str] = mapped_column(String(255))
    author_email: Mapped[str] = mapped_column(String(255))
    committed_at: Mapped[datetime] = mapped_column(DateTime)
    message: Mapped[str] = mapped_column(String(4096))
    parents_count: Mapped[int] = mapped_column(Integer, default=1)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    changed_files: Mapped[int] = mapped_column(Integer, default=0)
    branch_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)

    repository: Mapped[RepositoryORM] = relationship(back_populates="commits")
    contributor: Mapped[ContributorORM] = relationship(back_populates="commits")
    file_changes: Mapped[list["CommitFileORM"]] = relationship(back_populates="commit")


class BranchORM(Base):
    """Branch row."""

    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    name: Mapped[str] = mapped_column(String(255))
    is_local: Mapped[bool] = mapped_column(Boolean, default=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    head_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_unique_commit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ahead_count: Mapped[int] = mapped_column(Integer, default=0)
    behind_count: Mapped[int] = mapped_column(Integer, default=0)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    repository: Mapped[RepositoryORM] = relationship(back_populates="branches")


class FileORM(Base):
    """File row."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    path: Mapped[str] = mapped_column(String(2048), unique=True)
    extension: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    change_count: Mapped[int] = mapped_column(Integer, default=0)
    current_exists: Mapped[bool] = mapped_column(Boolean, default=True)

    repository: Mapped[RepositoryORM] = relationship(back_populates="files")
    commit_changes: Mapped[list["CommitFileORM"]] = relationship(back_populates="file")


class CommitFileORM(Base):
    """Join table between commits and files."""

    __tablename__ = "commit_files"

    commit_sha: Mapped[str] = mapped_column(ForeignKey("commits.sha"), primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), primary_key=True)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    change_type: Mapped[str] = mapped_column(String(32), default="modified")

    commit: Mapped[CommitORM] = relationship(back_populates="file_changes")
    file: Mapped[FileORM] = relationship(back_populates="commit_changes")


class TagORM(Base):
    """Tag row."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    name: Mapped[str] = mapped_column(String(255))
    target_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    repository: Mapped[RepositoryORM] = relationship(back_populates="tags")
