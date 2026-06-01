"""matplotlib 기반 차트 시각화.

가격/지표를 한 장의 차트로 그려 분석 결과를 직관적으로 보여준다.
matplotlib는 선택적 의존성이므로 함수 호출 시점에 지연 임포트한다.
헤드리스(서버) 환경에서도 동작하도록 'Agg' 백엔드를 사용한다.
"""

from __future__ import annotations

import pandas as pd

from ..models import AnalysisResult
from ..technical import indicators


def _ensure_backend():
    """GUI 없는 환경에서도 그릴 수 있도록 Agg 백엔드를 보장한다."""
    import matplotlib

    matplotlib.use("Agg", force=False)


def plot_analysis(
    close: pd.Series,
    result: AnalysisResult | None = None,
    *,
    save_path: str | None = None,
    show: bool = False,
):
    """가격 + 이동평균 + 볼린저밴드, RSI, MACD를 3단 차트로 그린다.

    Args:
        close: 종가 시리즈 (날짜 인덱스).
        result: 선택적 분석 결과. 있으면 제목에 추천/점수를 표시한다.
        save_path: 지정하면 해당 경로에 PNG로 저장한다.
        show: True면 plt.show()를 호출한다 (GUI 환경에서만 의미 있음).

    Returns:
        (figure, axes) 튜플.
    """
    _ensure_backend()
    import matplotlib.pyplot as plt

    sma20 = indicators.sma(close, 20)
    sma50 = indicators.sma(close, 50)
    bands = indicators.bollinger_bands(close, 20)
    rsi = indicators.rsi(close, 14)
    macd_df = indicators.macd(close)

    fig, axes = plt.subplots(
        3, 1, figsize=(12, 9), sharex=True, height_ratios=[3, 1, 1]
    )
    ax_price, ax_rsi, ax_macd = axes

    # --- 1단: 가격 + 이동평균 + 볼린저밴드 ---
    ax_price.plot(close.index, close, label="Close", color="black", linewidth=1.2)
    ax_price.plot(close.index, sma20, label="SMA 20", color="tab:blue", linewidth=0.9)
    ax_price.plot(close.index, sma50, label="SMA 50", color="tab:orange", linewidth=0.9)
    ax_price.plot(close.index, bands["upper"], color="gray", linewidth=0.7, linestyle="--")
    ax_price.plot(close.index, bands["lower"], color="gray", linewidth=0.7, linestyle="--")
    ax_price.fill_between(
        close.index, bands["lower"], bands["upper"], color="gray", alpha=0.12,
        label="Bollinger (20, 2σ)",
    )
    title = "Price & Indicators"
    if result is not None:
        title = (
            f"[{result.ticker}] {result.recommendation.value} "
            f"(score {result.composite_score:+.2f})"
        )
    ax_price.set_title(title)
    ax_price.set_ylabel("Price")
    ax_price.legend(loc="upper left", fontsize=8)
    ax_price.grid(True, alpha=0.3)

    # --- 2단: RSI ---
    ax_rsi.plot(close.index, rsi, color="tab:purple", linewidth=1.0)
    ax_rsi.axhline(70, color="red", linestyle="--", linewidth=0.7)
    ax_rsi.axhline(30, color="green", linestyle="--", linewidth=0.7)
    ax_rsi.set_ylim(0, 100)
    ax_rsi.set_ylabel("RSI")
    ax_rsi.grid(True, alpha=0.3)

    # --- 3단: MACD ---
    ax_macd.plot(close.index, macd_df["macd"], label="MACD", color="tab:blue", linewidth=0.9)
    ax_macd.plot(close.index, macd_df["signal"], label="Signal", color="tab:orange", linewidth=0.9)
    ax_macd.bar(
        close.index, macd_df["histogram"], color="gray", alpha=0.5, width=1.0,
        label="Histogram",
    )
    ax_macd.axhline(0, color="black", linewidth=0.6)
    ax_macd.set_ylabel("MACD")
    ax_macd.legend(loc="upper left", fontsize=8)
    ax_macd.grid(True, alpha=0.3)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
    if show:
        plt.show()
    return fig, axes
