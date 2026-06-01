"""포트폴리오 분석 검증 (네트워크 불필요)."""

from __future__ import annotations

import pandas as pd

from stock_analyzer import PortfolioAnalyzer, PortfolioResult
from stock_analyzer.data import DataProvider
from stock_analyzer.demo import DemoDataProvider, DemoNewsProvider
from stock_analyzer.sentiment import LexiconSentimentAnalyzer


class _BoomProvider(DataProvider):
    """특정 티커에서 예외를 던지는 제공자 (오류 처리 검증용)."""

    def __init__(self, base: DataProvider, boom: str):
        self._base = base
        self._boom = boom

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        if ticker == self._boom:
            raise ValueError("데이터 없음")
        return self._base.get_price_history(ticker, period)

    def get_fundamentals(self, ticker: str) -> dict:
        return self._base.get_fundamentals(ticker)


def test_portfolio_ranks_by_score():
    result = PortfolioAnalyzer(provider=DemoDataProvider()).analyze(
        ["AAPL", "MSFT", "NVDA", "TSLA"]
    )
    assert isinstance(result, PortfolioResult)
    assert len(result.results) == 4
    # 종합 점수 내림차순 정렬 확인
    scores = [r.composite_score for r in result.results]
    assert scores == sorted(scores, reverse=True)
    assert result.best is result.results[0]
    assert result.worst is result.results[-1]


def test_portfolio_deterministic():
    pa = PortfolioAnalyzer(provider=DemoDataProvider())
    first = [r.ticker for r in pa.analyze(["AAPL", "MSFT", "NVDA"]).results]
    second = [r.ticker for r in pa.analyze(["AAPL", "MSFT", "NVDA"]).results]
    assert first == second


def test_portfolio_with_news():
    result = PortfolioAnalyzer(
        provider=DemoDataProvider(),
        news_provider=DemoNewsProvider(),
        sentiment=LexiconSentimentAnalyzer(),
    ).analyze(["AAPL", "NVDA"])
    assert all(r.news_score is not None for r in result.results)


def test_portfolio_handles_errors():
    provider = _BoomProvider(DemoDataProvider(), boom="BAD")
    result = PortfolioAnalyzer(provider=provider).analyze(["AAPL", "BAD", "MSFT"])
    # 정상 2개만 결과에 포함, BAD는 errors에 기록
    assert len(result.results) == 2
    assert "BAD" in result.errors


def test_portfolio_summary_contains_ranking():
    result = PortfolioAnalyzer(provider=DemoDataProvider()).analyze(["AAPL", "MSFT"])
    summary = result.summary()
    assert "포트폴리오 분석" in summary
    assert "AAPL" in summary and "MSFT" in summary
