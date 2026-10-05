"""Data access infrastructure: one SQLite connection guarded by a re-entrant lock."""

import sqlite3
import threading
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    created_at    REAL    NOT NULL
);
CREATE TABLE courses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    instructor_id INTEGER NOT NULL REFERENCES users(id),
    capacity      INTEGER NOT NULL CHECK (capacity BETWEEN 1 AND 500),
    published     INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0, 1))
);
CREATE TABLE enrolments (
    course_id   INTEGER NOT NULL REFERENCES courses(id),
    student_id  INTEGER NOT NULL REFERENCES users(id),
    enrolled_at REAL    NOT NULL,
    PRIMARY KEY (course_id, student_id)
);
"""


class Database:
    def __init__(self, path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._lock = threading.RLock()

    @contextmanager
    def transaction(self):
        """Serialise access, commit on success and roll back on any error."""
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
