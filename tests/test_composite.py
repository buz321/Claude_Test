"""종합 점수 및 end-to-end 분석 검증 (mock provider 사용)."""

from __future__ import annotations

import pytest

from stock_analyzer import Recommendation, StockAnalyzer
from stock_analyzer.scoring import composite_score


def test_composite_weight_validation():
    with pytest.raises(ValueError):
        composite_score(0.5, 0.5, technical_weight=1.5)


def test_composite_weighting():
    # 기술적 +1, 기본적 -1, 가중치 0.5 → 0
    assert composite_score(1.0, -1.0, 0.5) == pytest.approx(0.0)
    # 기술적에 100% 가중 → 기술적 점수 그대로
    assert composite_score(0.8, -0.4, 1.0) == pytest.approx(0.8)


def test_recommendation_thresholds():
    assert Recommendation.from_score(0.6) == Recommendation.STRONG_BUY
    assert Recommendation.from_score(0.2) == Recommendation.BUY
    assert Recommendation.from_score(0.0) == Recommendation.HOLD
    assert Recommendation.from_score(-0.2) == Recommendation.SELL
    assert Recommendation.from_score(-0.6) == Recommendation.STRONG_SELL


def test_end_to_end_value_uptrend_is_bullish(uptrend_close, mock_provider_factory):
    """상승 추세 + 우량 재무 → 매수 계열 추천이 나와야 한다."""
    fundamentals = {
        "trailingPE": 12.0,
        "priceToBook": 0.9,
        "returnOnEquity": 0.22,
        "debtToEquity": 40.0,
        "profitMargins": 0.25,
    }
    provider = mock_provider_factory(uptrend_close, fundamentals)
    result = StockAnalyzer("TEST", provider=provider).analyze()

    assert result.composite_score > 0
    assert result.recommendation in (Recommendation.BUY, Recommendation.STRONG_BUY)
    assert result.reasons  # 근거가 비어있지 않아야 한다


def test_end_to_end_overvalued_downtrend_is_bearish(
    downtrend_close, mock_provider_factory
):
    """하락 추세 + 고평가 재무 → 매도 계열 추천이 나와야 한다."""
    fundamentals = {
        "trailingPE": 70.0,
        "priceToBook": 9.0,
        "returnOnEquity": -0.05,
        "debtToEquity": 280.0,
        "profitMargins": -0.1,
    }
    provider = mock_provider_factory(downtrend_close, fundamentals)
    result = StockAnalyzer("TEST", provider=provider).analyze()

    assert result.composite_score < 0
    assert result.recommendation in (Recommendation.SELL, Recommendation.STRONG_SELL)
