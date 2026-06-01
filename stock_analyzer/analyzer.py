"""고수준 파사드: 한 줄로 종목을 분석한다."""

from __future__ import annotations

from .data import DataProvider, YFinanceProvider
from .fundamental import extract_metrics, fundamental_signals
from .models import AnalysisResult, Signal
from .news import NewsProvider
from .scoring import average_score, recommend, weighted_score
from .sentiment import SentimentAnalyzer
from .technical import signals as tech_signals

# 종합 점수 기본 가중치. 뉴스 분석을 안 하면 news는 자동으로 빠지고 재정규화된다.
_DEFAULT_WEIGHTS = {"technical": 0.4, "fundamental": 0.4, "news": 0.2}


class StockAnalyzer:
    """주어진 티커에 대해 기술적/기본적/뉴스/종합 분석을 수행한다.

    예시::

        from stock_analyzer import StockAnalyzer

        result = StockAnalyzer("AAPL").analyze()
        print(result.summary())

        # 뉴스까지 반영해 등락 판단 (provider/sentiment 주입)
        from stock_analyzer.news import NewsApiProvider
        from stock_analyzer.sentiment import ClaudeSentimentAnalyzer
        result = StockAnalyzer(
            "NVDA",
            news_provider=NewsApiProvider(),
            sentiment=ClaudeSentimentAnalyzer(),
        ).analyze()

    테스트나 다른 데이터 소스를 쓰려면 각 provider 인자로 구현체를 주입한다.
    """

    def __init__(
        self,
        ticker: str,
        provider: DataProvider | None = None,
        *,
        news_provider: NewsProvider | None = None,
        sentiment: SentimentAnalyzer | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.ticker = ticker.upper()
        self.provider = provider or YFinanceProvider()
        self.news_provider = news_provider
        self.sentiment = sentiment
        self.weights = weights or dict(_DEFAULT_WEIGHTS)

    def analyze(self, period: str = "1y", *, news_limit: int = 15) -> AnalysisResult:
        """종목을 분석하고 AnalysisResult를 반환한다.

        news_provider와 sentiment가 모두 주입된 경우에만 뉴스 차원을 포함한다.
        """
        technical = self._technical_signals(period)
        fundamental = self._fundamental_signals()
        news, news_score = self._news_signals(news_limit)

        technical_score = average_score(technical)
        fundamental_score = average_score(fundamental)

        components = {
            "technical": technical_score,
            "fundamental": fundamental_score,
        }
        if news_score is not None:
            components["news"] = news_score

        total = weighted_score(components, self.weights)
        all_signals = technical + fundamental + news

        return AnalysisResult(
            ticker=self.ticker,
            recommendation=recommend(total),
            composite_score=total,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            news_score=news_score,
            signals=all_signals,
            reasons=[signal.reason for signal in all_signals],
        )

    def plot(
        self,
        period: str = "1y",
        *,
        save_path: str | None = None,
        show: bool = False,
    ):
        """종목을 분석하고 차트를 그린다.

        가격/이동평균/볼린저밴드, RSI, MACD를 3단 차트로 시각화하며
        제목에 추천 등급과 종합 점수를 표시한다.

        Args:
            period: 시세 조회 기간.
            save_path: 지정하면 해당 경로에 PNG로 저장한다.
            show: True면 plt.show() 호출 (GUI 환경 전용).

        Returns:
            (AnalysisResult, figure) 튜플.
        """
        from .viz import plot_analysis

        history = self.provider.get_price_history(self.ticker, period=period)
        close = history["Close"]
        result = self.analyze(period=period)
        fig, _ = plot_analysis(close, result, save_path=save_path, show=show)
        return result, fig

    def _technical_signals(self, period: str) -> list[Signal]:
        history = self.provider.get_price_history(self.ticker, period=period)
        close = history["Close"]
        return [
            tech_signals.rsi_signal(close),
            tech_signals.macd_signal(close),
            tech_signals.moving_average_signal(close),
            tech_signals.bollinger_signal(close),
        ]

    def _fundamental_signals(self) -> list[Signal]:
        fundamentals = self.provider.get_fundamentals(self.ticker)
        metrics = extract_metrics(fundamentals)
        return fundamental_signals(metrics)

    def _news_signals(self, limit: int) -> tuple[list[Signal], float | None]:
        """티커 관련 뉴스 감성을 집계해 단일 신호로 반환한다.

        news_provider/sentiment가 없으면 (빈 리스트, None)을 반환한다.
        """
        if self.news_provider is None or self.sentiment is None:
            return [], None

        articles = self.news_provider.get_news(self.ticker, limit=limit)
        if not articles:
            return [], None

        results = self.sentiment.analyze_many([a.text for a in articles])
        if not results:
            return [], None

        news_score = sum(r.score for r in results) / len(results)
        reason = (
            f"뉴스 {len(results)}건 평균 감성 {news_score:+.2f} "
            f"(긍정 {sum(1 for r in results if r.label == 'positive')}, "
            f"부정 {sum(1 for r in results if r.label == 'negative')})"
        )
        return [Signal("NEWS", news_score, reason)], news_score
