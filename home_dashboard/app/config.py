"""환경변수 기반 설정."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class Settings:
    """앱 전역 설정. 모든 값은 `HOME_` 접두어 환경변수로 덮어쓸 수 있습니다."""

    db_path: Path = field(default_factory=lambda: Path(_env("HOME_DB_PATH", "home.db")))
    host: str = field(default_factory=lambda: _env("HOME_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("HOME_PORT", 8000))
    timezone: str = field(default_factory=lambda: _env("HOME_TZ", "Asia/Seoul"))

    # 알림 채널: ntfy | telegram | console
    notify_channel: str = field(default_factory=lambda: _env("HOME_NOTIFY_CHANNEL", "console").lower())
    ntfy_server: str = field(default_factory=lambda: _env("HOME_NTFY_SERVER", "https://ntfy.sh"))
    ntfy_topic: str = field(default_factory=lambda: _env("HOME_NTFY_TOPIC"))
    ntfy_token: str = field(default_factory=lambda: _env("HOME_NTFY_TOKEN"))
    telegram_token: str = field(default_factory=lambda: _env("HOME_TELEGRAM_TOKEN"))
    telegram_chat_id: str = field(default_factory=lambda: _env("HOME_TELEGRAM_CHAT_ID"))

    # 아침 요약 알림 시각 (HH:MM)
    digest_time: str = field(default_factory=lambda: _env("HOME_DIGEST_TIME", "08:00"))
    # 일정 시작 몇 분 전에 미리 알릴지
    event_lead_minutes: int = field(default_factory=lambda: _env_int("HOME_EVENT_LEAD_MINUTES", 30))
    # 알림 스케줄러 사용 여부 (테스트에선 0)
    scheduler_enabled: bool = field(default_factory=lambda: _env("HOME_SCHEDULER", "1") != "0")

    @property
    def digest_hour_minute(self) -> tuple[int, int]:
        try:
            hour, minute = self.digest_time.split(":", 1)
            return int(hour), int(minute)
        except ValueError:
            return 8, 0


def load_settings() -> Settings:
    return Settings()
