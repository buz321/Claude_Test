"""기본적 분석 추출 및 점수화 검증."""

from __future__ import annotations

from stock_analyzer.fundamental import extract_metrics, fundamental_signals
from stock_analyzer.fundamental.metrics import FundamentalMetrics


def test_extract_metrics_handles_missing_and_invalid():
    raw = {
        "trailingPE": 18.0,
        "priceToBook": None,
        "returnOnEquity": "not-a-number",
        # debtToEquity 누락
        "profitMargins": 0.25,
    }
    metrics = extract_metrics(raw)
    assert metrics.pe_ratio == 18.0
    assert metrics.pb_ratio is None
    assert metrics.roe is None  # 변환 불가 → None
    assert metrics.debt_to_equity is None
    assert metrics.profit_margin == 0.25


def test_fundamental_signals_skip_none():
    metrics = FundamentalMetrics(pe_ratio=18.0)  # 나머지는 None
    signals = fundamental_signals(metrics)
    # PER 신호 하나만 생성되어야 한다.
    assert len(signals) == 1
    assert signals[0].name == "PER"


def test_strong_value_stock_scores_positive():
    metrics = FundamentalMetrics(
        pe_ratio=10.0,
        pb_ratio=0.8,
        roe=0.25,
        debt_to_equity=30.0,
        profit_margin=0.3,
    )
    signals = fundamental_signals(metrics)
    assert all(s.score > 0 for s in signals)


def test_overvalued_stock_scores_negative():
    metrics = FundamentalMetrics(
        pe_ratio=60.0,
        pb_ratio=8.0,
        roe=-0.05,
        debt_to_equity=300.0,
        profit_margin=-0.1,
    )
    signals = fundamental_signals(metrics)
    assert all(s.score < 0 for s in signals)
