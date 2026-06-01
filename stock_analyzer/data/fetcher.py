"""yfinance 기반 실데이터 제공자."""

from __future__ import annotations

import pandas as pd

from .base import DataProvider


class YFinanceProvider(DataProvider):
    """Yahoo Finance(yfinance)에서 시세와 재무 데이터를 가져오는 제공자.

    실행 시 외부 네트워크 접근이 필요하다. yfinance는 무거운 의존성이므로
    실제 호출 시점에 지연 임포트(lazy import)한다.
    """

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        import yfinance as yf

        data = yf.Ticker(ticker).history(period=period)
        if data is None or data.empty:
            raise ValueError(f"'{ticker}'의 시세 데이터를 가져오지 못했습니다.")
        return data

    def get_fundamentals(self, ticker: str) -> dict:
        import yfinance as yf

        info = yf.Ticker(ticker).info
        if not info:
            raise ValueError(f"'{ticker}'의 재무 데이터를 가져오지 못했습니다.")
        # 분석에 사용하는 핵심 지표만 추려서 반환한다.
        keys = [
            "trailingPE",
            "forwardPE",
            "priceToBook",
            "returnOnEquity",
            "debtToEquity",
            "profitMargins",
            "marketCap",
        ]
        return {key: info.get(key) for key in keys}
