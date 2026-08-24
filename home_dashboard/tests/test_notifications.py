"""알림 문구 생성 / 채널 선택 / 리마인더 스케줄 로직 테스트."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app import digest, repository
from app.config import Settings
from app.notifier import ConsoleNotifier, NtfyNotifier, TelegramNotifier, build_notifier
from app.repository import next_due_date
from app.scheduler import send_digest, send_due_reminders
from conftest import FakeNotifier

TZ = ZoneInfo("Asia/Seoul")


def test_build_notifier_picks_channel():
    assert isinstance(build_notifier(Settings(notify_channel="console")), ConsoleNotifier)
    assert isinstance(
        build_notifier(Settings(notify_channel="ntfy", ntfy_topic="our-home-abc")), NtfyNotifier
    )
    assert isinstance(
        build_notifier(Settings(notify_channel="telegram", telegram_token="t", telegram_chat_id="1")),
        TelegramNotifier,
    )


def test_build_notifier_falls_back_when_unconfigured():
    # 토픽/토큰이 비어 있으면 네트워크로 못 보내니 콘솔로 폴백합니다.
    assert isinstance(build_notifier(Settings(notify_channel="ntfy")), ConsoleNotifier)
    assert isinstance(build_notifier(Settings(notify_channel="telegram", telegram_token="t")), ConsoleNotifier)


def test_next_due_date():
    assert next_due_date("2026-08-24", "daily") == "2026-08-25"
    assert next_due_date("2026-08-24", "weekly") == "2026-08-31"
    assert next_due_date("2026-08-24", "monthly") == "2026-09-24"
    # 다음 달에 없는 날짜는 말일로 당깁니다.
    assert next_due_date("2026-01-31", "monthly") == "2026-02-28"
    assert next_due_date("2026-08-24", "none") == "2026-08-24"


def test_digest_contains_all_sections(conn):
    today = date(2026, 8, 24)
    repository.create_task(conn, {"title": "지난 할일", "due_date": "2026-08-20", "repeat": "none"})
    repository.create_task(
        conn, {"title": "분리수거", "due_date": today.isoformat(), "due_time": "20:00", "assignee": "아빠", "repeat": "weekly"}
    )
    repository.create_event(conn, {"title": "치과", "date": today.isoformat(), "start_time": "10:30", "location": "강남"})
    repository.create_event(conn, {"title": "아빠 생일", "date": "2026-08-28"})
    repository.create_shopping(conn, {"name": "우유"})

    title, body = digest.build_digest(repository.summary(conn, today))
    assert "8/24(월)" in title
    assert "지난 할일" in body
    assert "분리수거" in body and "20:00" in body and "아빠" in body
    assert "치과" in body and "@강남" in body
    assert "아빠 생일" in body and "8/28(금)" in body
    assert "우유" in body


def test_digest_handles_empty_day(conn):
    _, body = digest.build_digest(repository.summary(conn, date(2026, 8, 24)))
    assert body.count("• 없음") == 2


def test_send_digest_uses_notifier(conn):
    notifier = FakeNotifier()
    assert send_digest(conn, notifier, date(2026, 8, 24)) is True
    assert len(notifier.sent) == 1


def test_task_reminder_sent_once(conn):
    now = datetime(2026, 8, 24, 20, 1, tzinfo=TZ)
    repository.create_task(
        conn, {"title": "약 먹기", "due_date": "2026-08-24", "due_time": "20:00", "repeat": "none"}
    )
    notifier = FakeNotifier()

    assert send_due_reminders(conn, notifier, now, event_lead_minutes=30) == 1
    # 5분 뒤 스케줄러가 또 돌아도 같은 할일을 다시 보내지 않습니다.
    assert send_due_reminders(conn, notifier, now + timedelta(minutes=3), event_lead_minutes=30) == 0
    assert "약 먹기" in notifier.sent[0][1]


def test_task_reminder_not_sent_before_due_time(conn):
    repository.create_task(
        conn, {"title": "약 먹기", "due_date": "2026-08-24", "due_time": "20:00", "repeat": "none"}
    )
    notifier = FakeNotifier()
    now = datetime(2026, 8, 24, 19, 30, tzinfo=TZ)
    assert send_due_reminders(conn, notifier, now, event_lead_minutes=30) == 0


def test_event_reminder_within_lead_time(conn):
    repository.create_event(conn, {"title": "치과", "date": "2026-08-24", "start_time": "10:30"})
    notifier = FakeNotifier()

    early = datetime(2026, 8, 24, 9, 0, tzinfo=TZ)
    assert send_due_reminders(conn, notifier, early, event_lead_minutes=30) == 0

    close = datetime(2026, 8, 24, 10, 5, tzinfo=TZ)
    assert send_due_reminders(conn, notifier, close, event_lead_minutes=30) == 1
    assert "25분 뒤 치과" in notifier.sent[0][1]


def test_failed_send_is_not_counted(conn):
    repository.create_event(conn, {"title": "치과", "date": "2026-08-24", "start_time": "10:30"})
    notifier = FakeNotifier(ok=False)
    now = datetime(2026, 8, 24, 10, 5, tzinfo=TZ)
    assert send_due_reminders(conn, notifier, now, event_lead_minutes=30) == 0


def test_prune_notification_log(conn):
    assert repository.mark_notified(conn, "task:1:2026-08-24:20:00") is True
    assert repository.mark_notified(conn, "task:1:2026-08-24:20:00") is False
    conn.execute("UPDATE notification_log SET sent_at = '2000-01-01T00:00:00'")
    assert repository.prune_notification_log(conn, keep_days=14) == 1
