"""데이터 제공자(DataProvider) 추상 인터페이스.

실제 시세/재무 데이터 소스(yfinance 등)와 분석 로직을 분리하기 위한 계층.
테스트에서는 이 인터페이스를 구현한 mock provider를 주입해
네트워크 없이도 분석 로직을 검증할 수 있다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataProvider(ABC):
    """시세 및 재무 데이터를 제공하는 추상 클래스."""

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """OHLCV 시세 이력을 반환한다.

        Args:
            ticker: 주식 티커 (예: "AAPL").
            period: 조회 기간 (예: "1y", "6mo", "3mo").

        Returns:
            최소 'Close' 컬럼을 포함하는 DataFrame. 인덱스는 날짜.
            일반적으로 Open/High/Low/Close/Volume 컬럼을 가진다.
        """

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> dict:
        """재무 지표 딕셔너리를 반환한다.

        Args:
            ticker: 주식 티커.

        Returns:
            'trailingPE', 'priceToBook', 'returnOnEquity',
            'debtToEquity', 'profitMargins' 등의 키를 가질 수 있는 딕셔너리.
            값이 없는 항목은 누락되거나 None일 수 있다.
        """
