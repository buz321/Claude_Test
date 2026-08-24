"""SQLite 연결 및 스키마 관리 (외부 의존성 없이 stdlib만 사용)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    note         TEXT    NOT NULL DEFAULT '',
    assignee     TEXT    NOT NULL DEFAULT '',
    due_date     TEXT,
    due_time     TEXT,
    repeat       TEXT    NOT NULL DEFAULT 'none',
    done         INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS shopping_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    quantity   TEXT    NOT NULL DEFAULT '',
    note       TEXT    NOT NULL DEFAULT '',
    urgent     INTEGER NOT NULL DEFAULT 0,
    bought     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL,
    bought_at  TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    date       TEXT    NOT NULL,
    start_time TEXT,
    end_time   TEXT,
    location   TEXT    NOT NULL DEFAULT '',
    note       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL
);

-- 같은 알림을 중복 발송하지 않기 위한 기록
CREATE TABLE IF NOT EXISTS notification_log (
    key     TEXT PRIMARY KEY,
    sent_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_due   ON tasks(done, due_date);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    """WAL 모드로 연결한 커넥션을 돌려줍니다 (여러 기기 동시 접속에 유리)."""
    path = Path(db_path)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
