"""stock_analyzer 기본 사용 예시.

실제 Yahoo Finance 데이터로 종목을 분석한다 (네트워크 필요).
네트워크가 막힌 환경에서는 아래 '오프라인 데모'처럼 mock provider를 쓰면 된다.

실행:
    python examples/basic_usage.py AAPL MSFT
"""

from __future__ import annotations

import sys

from stock_analyzer import StockAnalyzer


def main(tickers: list[str]) -> None:
    for ticker in tickers:
        try:
            result = StockAnalyzer(ticker).analyze()
            print(result.summary())
        except Exception as exc:  # noqa: BLE001 - 데모 목적의 폭넓은 예외 처리
            print(f"[{ticker}] 분석 실패: {exc}")
        print("-" * 60)


if __name__ == "__main__":
    args = sys.argv[1:] or ["AAPL"]
    main(args)
