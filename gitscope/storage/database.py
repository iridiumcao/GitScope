"""SQLite engine and session factory helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from gitscope.storage.schema import Base


class SQLiteStoreEngine:
    """Owns the in-memory SQLite engine for one analysis run."""

    def __init__(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine, future=True, expire_on_commit=False)

    def session(self) -> Session:
        """Return a new SQLAlchemy session."""

        return self._session_factory()
