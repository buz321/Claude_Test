"""알림 문구 생성 (요약 다이제스트 / 개별 리마인더)."""

from __future__ import annotations

from datetime import date
from typing import Any

WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


def format_date(value: str) -> str:
    """'2026-08-24' → '8/24(월)'"""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return value
    return f"{parsed.month}/{parsed.day}({WEEKDAYS[parsed.weekday()]})"


def _task_line(task: dict[str, Any], with_date: bool = False) -> str:
    parts = [task["title"]]
    if with_date and task.get("due_date"):
        parts.append(f"({format_date(task['due_date'])})")
    if task.get("due_time"):
        parts.append(f"{task['due_time']}")
    if task.get("assignee"):
        parts.append(f"— {task['assignee']}")
    return "• " + " ".join(parts)


def _event_line(event: dict[str, Any], with_date: bool = False) -> str:
    parts = []
    if with_date:
        parts.append(format_date(event["date"]))
    if event.get("start_time"):
        parts.append(event["start_time"])
    parts.append(event["title"])
    if event.get("location"):
        parts.append(f"@{event['location']}")
    return "• " + " ".join(parts)


def build_digest(data: dict[str, Any]) -> tuple[str, str]:
    """아침 요약 알림의 (제목, 본문)."""
    counts = data["counts"]
    title = f"오늘의 집안일 {format_date(data['today'])}"
    lines: list[str] = []

    if data["overdue_tasks"]:
        lines.append(f"⚠️ 지난 할일 {counts['overdue']}건")
        lines += [_task_line(task, with_date=True) for task in data["overdue_tasks"]]
        lines.append("")

    lines.append(f"✅ 오늘 할일 {counts['today_tasks']}건")
    lines += [_task_line(task) for task in data["today_tasks"]] or ["• 없음"]
    lines.append("")

    lines.append(f"📅 오늘 일정 {counts['today_events']}건")
    lines += [_event_line(event) for event in data["today_events"]] or ["• 없음"]

    if data["week_events"]:
        lines.append("")
        lines.append("🗓 이번 주 일정")
        lines += [_event_line(event, with_date=True) for event in data["week_events"]]

    if data["shopping"]:
        lines.append("")
        names = ", ".join(item["name"] for item in data["shopping"][:10])
        more = "…" if len(data["shopping"]) > 10 else ""
        lines.append(f"🛒 살 것 {counts['shopping']}개: {names}{more}")

    return title, "\n".join(lines)


def build_task_reminder(task: dict[str, Any]) -> tuple[str, str]:
    who = f" ({task['assignee']})" if task.get("assignee") else ""
    when = f" {task['due_time']}" if task.get("due_time") else ""
    body = f"{task['title']}{when}{who}"
    if task.get("note"):
        body += f"\n{task['note']}"
    return "할일 알림", body


def build_event_reminder(event: dict[str, Any], minutes: int) -> tuple[str, str]:
    body = f"{minutes}분 뒤 {event['title']}"
    if event.get("start_time"):
        body += f" ({event['start_time']})"
    if event.get("location"):
        body += f"\n장소: {event['location']}"
    if event.get("note"):
        body += f"\n{event['note']}"
    return "일정 알림", body
