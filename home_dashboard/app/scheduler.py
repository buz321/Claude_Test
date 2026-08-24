"""알림 스케줄러: 아침 요약 + 마감/일정 임박 리마인더."""

from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from . import digest, repository
from .config import Settings
from .notifier import Notifier

logger = logging.getLogger(__name__)


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        hour, minute = value.split(":", 1)
        return time(int(hour), int(minute))
    except ValueError:
        return None


def send_digest(conn: sqlite3.Connection, notifier: Notifier, today: date) -> bool:
    """아침 요약 알림을 보냅니다."""
    data = repository.summary(conn, today)
    title, body = digest.build_digest(data)
    return notifier.send(title, body)


def send_due_reminders(
    conn: sqlite3.Connection,
    notifier: Notifier,
    now: datetime,
    event_lead_minutes: int,
    window_minutes: int = 5,
) -> int:
    """시간이 지정된 할일/일정 중 지금 알려야 할 것들을 발송합니다.

    같은 항목을 반복 발송하지 않도록 `notification_log` 로 중복을 막습니다.
    """
    sent = 0
    today = now.date()

    # 마감 시각이 지금 창(window) 안에 들어온 할일
    for task in repository.list_tasks(conn, include_done=False):
        due_time = _parse_time(task["due_time"])
        if not task["due_date"] or due_time is None:
            continue
        if task["due_date"] != today.isoformat():
            continue
        due_at = datetime.combine(today, due_time, tzinfo=now.tzinfo)
        if not (timedelta(0) <= now - due_at < timedelta(minutes=window_minutes)):
            continue
        key = f"task:{task['id']}:{task['due_date']}:{task['due_time']}"
        if not repository.mark_notified(conn, key):
            continue
        title, body = digest.build_task_reminder(task)
        if notifier.send(title, body, priority="high"):
            sent += 1

    # 시작 시각이 lead 분 이내로 다가온 일정
    for event in repository.list_events(conn, since=today.isoformat()):
        start_time = _parse_time(event["start_time"])
        if start_time is None or event["date"] != today.isoformat():
            continue
        starts_at = datetime.combine(today, start_time, tzinfo=now.tzinfo)
        remaining = starts_at - now
        if not (timedelta(0) <= remaining <= timedelta(minutes=event_lead_minutes)):
            continue
        key = f"event:{event['id']}:{event['date']}:{event['start_time']}"
        if not repository.mark_notified(conn, key):
            continue
        title, body = digest.build_event_reminder(event, max(1, int(remaining.total_seconds() // 60)))
        if notifier.send(title, body, priority="high"):
            sent += 1

    return sent


def start_scheduler(
    conn: sqlite3.Connection, notifier: Notifier, settings: Settings
) -> BackgroundScheduler:
    """백그라운드 스케줄러를 시작합니다 (앱 기동 시 1회)."""
    tz = ZoneInfo(settings.timezone)
    scheduler = BackgroundScheduler(timezone=tz)
    hour, minute = settings.digest_hour_minute

    scheduler.add_job(
        lambda: send_digest(conn, notifier, datetime.now(tz).date()),
        trigger="cron",
        hour=hour,
        minute=minute,
        id="daily_digest",
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        lambda: send_due_reminders(conn, notifier, datetime.now(tz), settings.event_lead_minutes),
        trigger="interval",
        minutes=5,
        id="due_reminders",
        misfire_grace_time=300,
    )
    scheduler.add_job(
        lambda: repository.prune_notification_log(conn),
        trigger="cron",
        hour=4,
        id="prune_log",
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info(
        "스케줄러 시작: 아침 요약 %02d:%02d, 일정 %d분 전 알림, 채널=%s",
        hour,
        minute,
        settings.event_lead_minutes,
        notifier.name,
    )
    return scheduler
