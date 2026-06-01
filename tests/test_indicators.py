"""기술적 지표 계산 검증."""

from __future__ import annotations

import numpy as np
import pandas as pd

from stock_analyzer.technical import indicators


def test_sma_of_constant_is_constant():
    series = pd.Series([5.0] * 30)
    result = indicators.sma(series, window=10)
    # 워밍업 구간 이후 값은 모두 입력 상수와 같아야 한다.
    assert result.dropna().eq(5.0).all()


def test_ema_tracks_constant():
    series = pd.Series([7.0] * 50)
    result = indicators.ema(series, window=10)
    assert np.isclose(result.iloc[-1], 7.0)


def test_rsi_bounds_and_uptrend():
    # 단조 증가 → 손실이 없어 RSI는 100에 가까워야 한다.
    series = pd.Series(np.linspace(100, 200, 100))
    result = indicators.rsi(series, window=14).dropna()
    assert (result >= 0).all() and (result <= 100).all()
    assert result.iloc[-1] > 95


def test_rsi_downtrend():
    series = pd.Series(np.linspace(200, 100, 100))
    result = indicators.rsi(series, window=14).dropna()
    assert result.iloc[-1] < 5


def test_macd_columns():
    series = pd.Series(np.linspace(100, 200, 100))
    result = indicators.macd(series)
    assert list(result.columns) == ["macd", "signal", "histogram"]
    # 상승 추세에서는 MACD가 양수여야 한다.
    assert result["macd"].iloc[-1] > 0


def test_bollinger_band_ordering():
    series = pd.Series(np.random.default_rng(0).normal(100, 5, 100))
    bands = indicators.bollinger_bands(series, window=20).dropna()
    assert (bands["upper"] >= bands["middle"]).all()
    assert (bands["middle"] >= bands["lower"]).all()
