"""SQLite 데이터 접근 계층 (CRUD + 대시보드 조회)."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Any

Row = dict[str, Any]

_TASK_FIELDS = ("title", "note", "assignee", "due_date", "due_time", "repeat")
_SHOPPING_FIELDS = ("name", "quantity", "note", "urgent")
_EVENT_FIELDS = ("title", "date", "start_time", "end_time", "location", "note")


def _rows(cursor: sqlite3.Cursor) -> list[Row]:
    return [dict(row) for row in cursor.fetchall()]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def next_due_date(due_date: str, repeat: str) -> str:
    """반복 할일을 완료했을 때 다음 마감일을 계산합니다."""
    current = date.fromisoformat(due_date)
    if repeat == "daily":
        return (current + timedelta(days=1)).isoformat()
    if repeat == "weekly":
        return (current + timedelta(days=7)).isoformat()
    if repeat == "monthly":
        year, month = current.year, current.month + 1
        if month > 12:
            year, month = year + 1, 1
        # 31일 → 다음 달에 없으면 말일로 당깁니다.
        day = current.day
        while day > 28:
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                day -= 1
        return date(year, month, day).isoformat()
    return due_date


# --------------------------------------------------------------------------- 할일


def list_tasks(conn: sqlite3.Connection, include_done: bool = True) -> list[Row]:
    sql = "SELECT * FROM tasks"
    if not include_done:
        sql += " WHERE done = 0"
    sql += " ORDER BY done, due_date IS NULL, due_date, due_time IS NULL, due_time, id"
    return _rows(conn.execute(sql))


def get_task(conn: sqlite3.Connection, task_id: int) -> Row | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


_TASK_DEFAULTS = {"note": "", "assignee": "", "repeat": "none"}
_EVENT_DEFAULTS = {"location": "", "note": ""}


def create_task(conn: sqlite3.Connection, data: dict[str, Any]) -> Row:
    values = [data.get(field) or _TASK_DEFAULTS.get(field) for field in _TASK_FIELDS]
    cursor = conn.execute(
        "INSERT INTO tasks (title, note, assignee, due_date, due_time, repeat, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (*values, _now()),
    )
    conn.commit()
    return get_task(conn, int(cursor.lastrowid))  # type: ignore[return-value]


def update_task(conn: sqlite3.Connection, task_id: int, patch: dict[str, Any]) -> Row | None:
    task = get_task(conn, task_id)
    if task is None:
        return None

    if patch.get("done") is True and not task["done"]:
        # 반복 할일은 완료 대신 다음 주기로 넘깁니다.
        if task["repeat"] != "none" and task["due_date"]:
            conn.execute(
                "UPDATE tasks SET due_date = ?, done = 0, completed_at = ? WHERE id = ?",
                (next_due_date(task["due_date"], task["repeat"]), _now(), task_id),
            )
            conn.commit()
            return get_task(conn, task_id)
        patch = {**patch, "completed_at": _now()}
    elif patch.get("done") is False:
        patch = {**patch, "completed_at": None}

    fields: dict[str, Any] = {
        key: value for key, value in patch.items() if key in _TASK_FIELDS and value is not None
    }
    if patch.get("done") is not None:
        fields["done"] = int(bool(patch["done"]))
        fields["completed_at"] = patch.get("completed_at")
    if not fields:
        return task

    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", (*fields.values(), task_id))
    conn.commit()
    return get_task(conn, task_id)


def delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return cursor.rowcount > 0


# ------------------------------------------------------------------------- 장보기


def list_shopping(conn: sqlite3.Connection) -> list[Row]:
    return _rows(
        conn.execute("SELECT * FROM shopping_items ORDER BY bought, urgent DESC, id")
    )


def get_shopping(conn: sqlite3.Connection, item_id: int) -> Row | None:
    row = conn.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def create_shopping(conn: sqlite3.Connection, data: dict[str, Any]) -> Row:
    cursor = conn.execute(
        "INSERT INTO shopping_items (name, quantity, note, urgent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("quantity", ""),
            data.get("note", ""),
            int(bool(data.get("urgent"))),
            _now(),
        ),
    )
    conn.commit()
    return get_shopping(conn, int(cursor.lastrowid))  # type: ignore[return-value]


def update_shopping(conn: sqlite3.Connection, item_id: int, patch: dict[str, Any]) -> Row | None:
    item = get_shopping(conn, item_id)
    if item is None:
        return None

    fields = {key: value for key, value in patch.items() if key in _SHOPPING_FIELDS and value is not None}
    if "urgent" in fields:
        fields["urgent"] = int(bool(fields["urgent"]))
    if patch.get("bought") is not None:
        fields["bought"] = int(bool(patch["bought"]))
        fields["bought_at"] = _now() if patch["bought"] else None
    if not fields:
        return item

    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE shopping_items SET {assignments} WHERE id = ?", (*fields.values(), item_id))
    conn.commit()
    return get_shopping(conn, item_id)


def delete_shopping(conn: sqlite3.Connection, item_id: int) -> bool:
    cursor = conn.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
    conn.commit()
    return cursor.rowcount > 0


def clear_bought(conn: sqlite3.Connection) -> int:
    cursor = conn.execute("DELETE FROM shopping_items WHERE bought = 1")
    conn.commit()
    return cursor.rowcount


# --------------------------------------------------------------------------- 일정


def list_events(conn: sqlite3.Connection, since: str | None = None) -> list[Row]:
    if since:
        sql = "SELECT * FROM events WHERE date >= ? ORDER BY date, start_time IS NULL, start_time, id"
        return _rows(conn.execute(sql, (since,)))
    return _rows(conn.execute("SELECT * FROM events ORDER BY date, start_time IS NULL, start_time, id"))


def get_event(conn: sqlite3.Connection, event_id: int) -> Row | None:
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return dict(row) if row else None


def create_event(conn: sqlite3.Connection, data: dict[str, Any]) -> Row:
    values = [data.get(field) or _EVENT_DEFAULTS.get(field) for field in _EVENT_FIELDS]
    cursor = conn.execute(
        "INSERT INTO events (title, date, start_time, end_time, location, note, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (*values, _now()),
    )
    conn.commit()
    return get_event(conn, int(cursor.lastrowid))  # type: ignore[return-value]


def update_event(conn: sqlite3.Connection, event_id: int, patch: dict[str, Any]) -> Row | None:
    event = get_event(conn, event_id)
    if event is None:
        return None
    fields = {key: value for key, value in patch.items() if key in _EVENT_FIELDS and value is not None}
    if not fields:
        return event
    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE events SET {assignments} WHERE id = ?", (*fields.values(), event_id))
    conn.commit()
    return get_event(conn, event_id)


def delete_event(conn: sqlite3.Connection, event_id: int) -> bool:
    cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    return cursor.rowcount > 0


# ----------------------------------------------------------------------- 대시보드


def summary(conn: sqlite3.Connection, today: date, week_days: int = 7) -> dict[str, Any]:
    """오늘 화면에 필요한 데이터를 한 번에 모아줍니다."""
    today_str = today.isoformat()
    week_end = (today + timedelta(days=week_days)).isoformat()

    overdue = _rows(
        conn.execute(
            "SELECT * FROM tasks WHERE done = 0 AND due_date IS NOT NULL AND due_date < ?"
            " ORDER BY due_date, due_time IS NULL, due_time",
            (today_str,),
        )
    )
    today_tasks = _rows(
        conn.execute(
            "SELECT * FROM tasks WHERE done = 0 AND due_date = ? ORDER BY due_time IS NULL, due_time",
            (today_str,),
        )
    )
    upcoming_tasks = _rows(
        conn.execute(
            "SELECT * FROM tasks WHERE done = 0 AND due_date > ? AND due_date <= ?"
            " ORDER BY due_date, due_time IS NULL, due_time",
            (today_str, week_end),
        )
    )
    someday_tasks = _rows(
        conn.execute("SELECT * FROM tasks WHERE done = 0 AND due_date IS NULL ORDER BY id")
    )
    today_events = _rows(
        conn.execute(
            "SELECT * FROM events WHERE date = ? ORDER BY start_time IS NULL, start_time",
            (today_str,),
        )
    )
    week_events = _rows(
        conn.execute(
            "SELECT * FROM events WHERE date > ? AND date <= ? ORDER BY date, start_time IS NULL, start_time",
            (today_str, week_end),
        )
    )
    shopping = _rows(
        conn.execute("SELECT * FROM shopping_items WHERE bought = 0 ORDER BY urgent DESC, id")
    )

    return {
        "today": today_str,
        "overdue_tasks": overdue,
        "today_tasks": today_tasks,
        "upcoming_tasks": upcoming_tasks,
        "someday_tasks": someday_tasks,
        "today_events": today_events,
        "week_events": week_events,
        "shopping": shopping,
        "counts": {
            "overdue": len(overdue),
            "today_tasks": len(today_tasks),
            "today_events": len(today_events),
            "shopping": len(shopping),
        },
    }


# --------------------------------------------------------------------- 알림 중복방지


def mark_notified(conn: sqlite3.Connection, key: str) -> bool:
    """처음 보내는 알림이면 True. 이미 보낸 적 있으면 False."""
    try:
        conn.execute("INSERT INTO notification_log (key, sent_at) VALUES (?, ?)", (key, _now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def prune_notification_log(conn: sqlite3.Connection, keep_days: int = 14) -> int:
    cutoff = (datetime.now() - timedelta(days=keep_days)).isoformat(timespec="seconds")
    cursor = conn.execute("DELETE FROM notification_log WHERE sent_at < ?", (cutoff,))
    conn.commit()
    return cursor.rowcount
