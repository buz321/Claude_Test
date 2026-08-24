import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.db import connect, init_db  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(db_path=tmp_path / "test.db", scheduler_enabled=False, notify_channel="console")


@pytest.fixture
def conn(settings):
    connection = connect(settings.db_path)
    init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


class FakeNotifier:
    """발송 내용을 기록만 하는 테스트용 알림 채널."""

    name = "fake"

    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.sent: list[tuple[str, str, str]] = []

    def send(self, title: str, message: str, priority: str = "default") -> bool:
        self.sent.append((title, message, priority))
        return self.ok
