"""차트 시각화 데모 (네트워크 불필요).

mock 데이터로 분석 + 3단 차트를 생성해 PNG로 저장한다.
실데이터로 보려면 DemoProvider 대신 기본 YFinanceProvider를 쓰면 된다
(네트워크 허용 환경에서):

    StockAnalyzer("AAPL").plot(save_path="aapl.png")

실행:
    python examples/plot_demo.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stock_analyzer import StockAnalyzer
from stock_analyzer.data import DataProvider


class DemoProvider(DataProvider):
    """결정론적 가짜 데이터를 반환하는 데모용 제공자."""

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        dates = pd.date_range("2024-01-01", periods=250, freq="B")
        rng = np.random.default_rng(7)
        trend = np.concatenate(
            [np.linspace(150, 210, 150), np.linspace(210, 190, 100)]
        )
        price = trend + np.cumsum(rng.normal(0, 1.2, 250))
        return pd.DataFrame({"Close": price}, index=dates)

    def get_fundamentals(self, ticker: str) -> dict:
        return {
            "trailingPE": 16.0,
            "priceToBook": 2.4,
            "returnOnEquity": 0.19,
            "debtToEquity": 60.0,
            "profitMargins": 0.18,
        }


def main() -> None:
    analyzer = StockAnalyzer("DEMO", provider=DemoProvider())
    result, _ = analyzer.plot(save_path="demo_chart.png")
    print(result.summary())
    print("\n차트 저장: demo_chart.png")


if __name__ == "__main__":
    main()
