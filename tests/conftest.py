"""테스트용 공용 fixture.

네트워크 없이 분석 로직을 검증하기 위해 결정론적 샘플 데이터와
mock DataProvider를 제공한다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stock_analyzer.data import DataProvider


@pytest.fixture
def uptrend_close() -> pd.Series:
    """완만하게 상승하는 종가 시리즈 (250 거래일)."""
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    values = np.linspace(100, 200, 250)
    return pd.Series(values, index=dates, name="Close")


@pytest.fixture
def downtrend_close() -> pd.Series:
    """완만하게 하락하는 종가 시리즈 (250 거래일)."""
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    values = np.linspace(200, 100, 250)
    return pd.Series(values, index=dates, name="Close")


class MockProvider(DataProvider):
    """주입된 종가 시리즈와 재무 딕셔너리를 그대로 반환하는 테스트용 제공자."""

    def __init__(self, close: pd.Series, fundamentals: dict) -> None:
        self._close = close
        self._fundamentals = fundamentals

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        return pd.DataFrame({"Close": self._close})

    def get_fundamentals(self, ticker: str) -> dict:
        return dict(self._fundamentals)


@pytest.fixture
def mock_provider_factory():
    """MockProvider를 만드는 팩토리를 반환한다."""

    def _make(close: pd.Series, fundamentals: dict | None = None) -> MockProvider:
        return MockProvider(close, fundamentals or {})

    return _make
