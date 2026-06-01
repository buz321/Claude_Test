"""포트폴리오 분석: 여러 종목을 분석해 종합 점수로 순위를 매긴다."""

from __future__ import annotations

from .analyzer import StockAnalyzer
from .data import DataProvider
from .models import PortfolioResult
from .news import NewsProvider
from .sentiment import SentimentAnalyzer


class PortfolioAnalyzer:
    """여러 종목을 같은 기준으로 분석하고 순위를 매기는 파사드.

    예시::

        from stock_analyzer import PortfolioAnalyzer

        result = PortfolioAnalyzer().analyze(["AAPL", "MSFT", "NVDA"])
        print(result.summary())   # 종합 점수 순 순위표
        print(result.best.ticker) # 최상위 종목

    provider/news_provider/sentiment는 모든 종목에 공유된다.
    뉴스 provider는 종목 티커를 질의어로 받아야 하므로 NewsApiProvider처럼
    임의 질의를 처리할 수 있는 구현이어야 한다.
    """

    def __init__(
        self,
        provider: DataProvider | None = None,
        *,
        news_provider: NewsProvider | None = None,
        sentiment: SentimentAnalyzer | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.provider = provider
        self.news_provider = news_provider
        self.sentiment = sentiment
        self.weights = weights

    def analyze(self, tickers: list[str], period: str = "1y") -> PortfolioResult:
        """종목 목록을 분석하고 종합 점수 내림차순으로 정렬해 반환한다.

        개별 종목 분석이 실패하면 건너뛰고 errors에 기록한다.
        """
        results = []
        errors: dict[str, str] = {}
        for ticker in tickers:
            try:
                analyzer = StockAnalyzer(
                    ticker,
                    provider=self.provider,
                    news_provider=self.news_provider,
                    sentiment=self.sentiment,
                    weights=self.weights,
                )
                results.append(analyzer.analyze(period=period))
            except Exception as exc:  # noqa: BLE001 - 한 종목 실패가 전체를 막지 않도록
                errors[ticker.upper()] = str(exc)

        results.sort(key=lambda r: r.composite_score, reverse=True)
        return PortfolioResult(results=results, errors=errors)
