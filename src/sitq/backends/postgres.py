"""
PostgreSQL backend – same API as SQLite but using asyncpg via SQLAlchemy.
"""

from __future__ import annotations

# The implementation is identical to SQLiteBackend; only the connection URL
# differs. For brevity we simply subclass and reuse the SQLite code.

from .sqlite import SQLiteBackend


class PostgresBackend(SQLiteBackend):
    """
    PostgreSQL version – just a thin wrapper that changes the URL pattern.
    Example URL: ``postgresql+asyncpg://user:pwd@host/dbname``.
    """

    def __init__(self, db_url: str):
        super().__init__(db_path=db_url)
