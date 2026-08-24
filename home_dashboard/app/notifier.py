"""핸드폰 푸시 알림 발송 (ntfy / 텔레그램 / 콘솔)."""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

TIMEOUT = 10.0


class Notifier(Protocol):
    """알림 채널 공통 인터페이스."""

    name: str

    def send(self, title: str, message: str, priority: str = "default") -> bool:
        ...


class ConsoleNotifier:
    """설정이 없을 때 쓰는 기본값. 로그로만 남깁니다."""

    name = "console"

    def send(self, title: str, message: str, priority: str = "default") -> bool:
        logger.info("[알림:%s] %s\n%s", priority, title, message)
        return True


class NtfyNotifier:
    """ntfy.sh (또는 자체 호스팅 ntfy) 로 푸시. 앱에서 토픽만 구독하면 끝."""

    name = "ntfy"

    def __init__(self, server: str, topic: str, token: str = "") -> None:
        self.server = server.rstrip("/")
        self.topic = topic
        self.token = token

    def send(self, title: str, message: str, priority: str = "default") -> bool:
        headers = {
            "Title": title.encode("utf-8").decode("latin-1", "ignore") or "집안 대시보드",
            "Priority": priority,
            "Markdown": "yes",
        }
        # ntfy 헤더는 ASCII만 안전하므로 한글 제목은 본문 첫 줄로 넣습니다.
        if not title.isascii():
            headers["Title"] = "Home Dashboard"
            message = f"**{title}**\n\n{message}"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = httpx.post(
                f"{self.server}/{self.topic}",
                content=message.encode("utf-8"),
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.error("ntfy 발송 실패: %s", exc)
            return False


class TelegramNotifier:
    """텔레그램 봇으로 푸시. 봇 토큰과 chat_id 필요."""

    name = "telegram"

    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id

    def send(self, title: str, message: str, priority: str = "default") -> bool:
        try:
            response = httpx.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": f"*{title}*\n\n{message}",
                    "parse_mode": "Markdown",
                    "disable_notification": priority == "low",
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.error("텔레그램 발송 실패: %s", exc)
            return False


def build_notifier(settings: Settings) -> Notifier:
    """설정에 맞는 알림 채널을 만들어 줍니다. 값이 비어 있으면 콘솔로 폴백."""
    channel = settings.notify_channel
    if channel == "ntfy" and settings.ntfy_topic:
        return NtfyNotifier(settings.ntfy_server, settings.ntfy_topic, settings.ntfy_token)
    if channel == "telegram" and settings.telegram_token and settings.telegram_chat_id:
        return TelegramNotifier(settings.telegram_token, settings.telegram_chat_id)
    if channel not in ("console", ""):
        logger.warning("알림 채널 '%s' 설정이 비어 있어 콘솔로 대체합니다.", channel)
    return ConsoleNotifier()
