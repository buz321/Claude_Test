"""기술적 지표 계산 함수.

모든 함수는 pandas Series를 입력받아 pandas 객체를 반환하는 순수 함수다.
외부 의존성을 최소화하기 위해 pandas/numpy만으로 직접 구현했다.
"""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int = 20) -> pd.Series:
    """단순 이동평균(Simple Moving Average)."""
    return series.rolling(window=window).mean()


def ema(series: pd.Series, window: int = 20) -> pd.Series:
    """지수 이동평균(Exponential Moving Average)."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """상대강도지수(Relative Strength Index), 0~100 범위.

    Wilder의 평활 이동평균(EMA, alpha=1/window)을 사용해 계산한다.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    # 손실이 0이면 rs가 무한대가 되어 RSI=100, 둘 다 0이면 NaN → 중립(50)으로 처리.
    rsi_values = rsi_values.where(avg_loss != 0, 100.0)
    rsi_values = rsi_values.mask((avg_gain == 0) & (avg_loss == 0), 50.0)
    return rsi_values


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD 지표.

    Returns:
        'macd', 'signal', 'histogram' 컬럼을 가진 DataFrame.
    """
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}
    )


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """볼린저 밴드.

    Returns:
        'middle', 'upper', 'lower' 컬럼을 가진 DataFrame.
    """
    middle = sma(series, window)
    std = series.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return pd.DataFrame({"middle": middle, "upper": upper, "lower": lower})
