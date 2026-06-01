"""기술적 지표를 매수/매도 신호로 해석한다.

각 함수는 최신 시점의 지표 값을 보고 -1.0(강한 매도)~+1.0(강한 매수)
범위의 Signal을 반환한다.
"""

from __future__ import annotations

import pandas as pd

from ..models import Signal
from . import indicators


def _last_valid(series: pd.Series) -> float | None:
    """NaN을 제외한 가장 마지막 유효 값을 반환한다."""
    valid = series.dropna()
    if valid.empty:
        return None
    return float(valid.iloc[-1])


def rsi_signal(close: pd.Series, window: int = 14) -> Signal:
    """RSI 기반 신호. 과매도(<30)면 매수, 과매수(>70)면 매도."""
    value = _last_valid(indicators.rsi(close, window))
    if value is None:
        return Signal("RSI", 0.0, "RSI 계산에 필요한 데이터 부족")

    if value < 30:
        # 30 → +1.0 에 가깝게, 0 → +1.0
        score = min(1.0, (30 - value) / 30 + 0.5)
        return Signal("RSI", score, f"RSI {value:.1f} → 과매도 구간(매수 신호)")
    if value > 70:
        score = -min(1.0, (value - 70) / 30 + 0.5)
        return Signal("RSI", score, f"RSI {value:.1f} → 과매수 구간(매도 신호)")
    # 50을 중립으로 보고 30~70 구간을 완만히 점수화.
    score = (50 - value) / 40
    return Signal("RSI", score, f"RSI {value:.1f} → 중립 구간")


def macd_signal(close: pd.Series) -> Signal:
    """MACD 히스토그램 부호로 추세 신호 판단."""
    hist = indicators.macd(close)["histogram"]
    value = _last_valid(hist)
    if value is None:
        return Signal("MACD", 0.0, "MACD 계산에 필요한 데이터 부족")

    if value > 0:
        return Signal("MACD", 0.5, f"MACD 히스토그램 {value:+.3f} → 상승 추세")
    if value < 0:
        return Signal("MACD", -0.5, f"MACD 히스토그램 {value:+.3f} → 하락 추세")
    return Signal("MACD", 0.0, "MACD 히스토그램 0 → 중립")


def moving_average_signal(close: pd.Series, short: int = 50, long: int = 200) -> Signal:
    """단기/장기 이동평균 교차(골든/데드크로스) 신호."""
    short_ma = _last_valid(indicators.sma(close, short))
    long_ma = _last_valid(indicators.sma(close, long))
    if short_ma is None or long_ma is None:
        return Signal("MA_CROSS", 0.0, "이동평균 계산에 필요한 데이터 부족")

    if short_ma > long_ma:
        return Signal(
            "MA_CROSS",
            0.5,
            f"단기 MA({short}) > 장기 MA({long}) → 골든크로스(상승)",
        )
    if short_ma < long_ma:
        return Signal(
            "MA_CROSS",
            -0.5,
            f"단기 MA({short}) < 장기 MA({long}) → 데드크로스(하락)",
        )
    return Signal("MA_CROSS", 0.0, "단기/장기 이동평균 동일 → 중립")


def bollinger_signal(close: pd.Series, window: int = 20, num_std: float = 2.0) -> Signal:
    """볼린저 밴드 위치로 신호 판단. 하단 이탈은 매수, 상단 이탈은 매도."""
    bands = indicators.bollinger_bands(close, window, num_std)
    price = _last_valid(close)
    upper = _last_valid(bands["upper"])
    lower = _last_valid(bands["lower"])
    if price is None or upper is None or lower is None:
        return Signal("BOLLINGER", 0.0, "볼린저 밴드 계산에 필요한 데이터 부족")

    if price <= lower:
        return Signal("BOLLINGER", 0.6, f"가격이 하단밴드({lower:.2f}) 이하 → 매수 신호")
    if price >= upper:
        return Signal("BOLLINGER", -0.6, f"가격이 상단밴드({upper:.2f}) 이상 → 매도 신호")
    return Signal("BOLLINGER", 0.0, "가격이 밴드 내부 → 중립")
