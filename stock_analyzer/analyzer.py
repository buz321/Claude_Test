"""고수준 파사드: 한 줄로 종목을 분석한다."""

from __future__ import annotations

from .data import DataProvider, YFinanceProvider
from .fundamental import extract_metrics, fundamental_signals
from .models import AnalysisResult, Signal
from .scoring import average_score, composite_score, recommend
from .technical import signals as tech_signals


class StockAnalyzer:
    """주어진 티커에 대해 기술적/기본적/종합 분석을 수행한다.

    예시::

        from stock_analyzer import StockAnalyzer

        result = StockAnalyzer("AAPL").analyze()
        print(result.summary())

    테스트나 다른 데이터 소스를 쓰려면 `provider` 인자로
    DataProvider 구현체를 주입하면 된다.
    """

    def __init__(
        self,
        ticker: str,
        provider: DataProvider | None = None,
        technical_weight: float = 0.5,
    ) -> None:
        self.ticker = ticker.upper()
        self.provider = provider or YFinanceProvider()
        self.technical_weight = technical_weight

    def analyze(self, period: str = "1y") -> AnalysisResult:
        """종목을 분석하고 AnalysisResult를 반환한다."""
        technical = self._technical_signals(period)
        fundamental = self._fundamental_signals()

        technical_score = average_score(technical)
        fundamental_score = average_score(fundamental)
        total = composite_score(
            technical_score, fundamental_score, self.technical_weight
        )

        all_signals = technical + fundamental
        return AnalysisResult(
            ticker=self.ticker,
            recommendation=recommend(total),
            composite_score=total,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
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
