"""뉴스 수집, 사전 감성, 다이제스트, 종목 뉴스 통합 검증 (네트워크 불필요)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest

from stock_analyzer import NewsAnalyzer, Recommendation, StockAnalyzer
from stock_analyzer.news import MockNewsProvider, NewsArticle
from stock_analyzer.sentiment import LexiconSentimentAnalyzer


@pytest.fixture
def sample_articles() -> list[NewsArticle]:
    return [
        NewsArticle(
            title="AI chip demand surges as profits beat estimates",
            summary="Record growth and strong earnings boost the sector.",
            source="TestWire",
            published_at=datetime(2026, 6, 1, 9, 0),
        ),
        NewsArticle(
            title="AI startup faces lawsuit and probe over fraud",
            summary="Concerns and warnings weigh on the stock, shares plunge.",
            source="TestWire",
            published_at=datetime(2026, 6, 1, 10, 0),
        ),
        NewsArticle(
            title="New AI model released to the public",
            summary="The company announced a new model today.",
            source="TestWire",
            published_at=datetime(2026, 6, 1, 11, 0),
        ),
    ]


def test_lexicon_positive_and_negative():
    analyzer = LexiconSentimentAnalyzer()
    pos = analyzer.analyze("Stock surges on record profit and strong growth")
    neg = analyzer.analyze("Shares plunge on lawsuit, fraud probe and losses")
    neutral = analyzer.analyze("The company held a meeting on Tuesday")

    assert pos.score > 0 and pos.label == "positive"
    assert neg.score < 0 and neg.label == "negative"
    assert neutral.label == "neutral"


def test_mock_provider_filters_by_query_and_date(sample_articles):
    provider = MockNewsProvider(sample_articles)
    # 모두 "AI"를 포함
    assert len(provider.get_news("AI")) == 3
    # 존재하지 않는 키워드
    assert provider.get_news("crypto") == []


def test_news_digest(sample_articles):
    na = NewsAnalyzer(
        provider=MockNewsProvider(sample_articles),
        sentiment=LexiconSentimentAnalyzer(),
    )
    digest = na.digest("AI")

    assert digest.topic == "AI"
    assert digest.article_count == 3
    assert digest.overall_label in ("positive", "negative", "neutral")
    assert len(digest.headlines) == 3
    assert digest.market_impact  # 비어있지 않음


def test_news_digest_empty():
    na = NewsAnalyzer(
        provider=MockNewsProvider([]),
        sentiment=LexiconSentimentAnalyzer(),
    )
    digest = na.digest("nothing")
    assert digest.article_count == 0
    assert digest.overall_label == "neutral"


def test_stock_analyzer_includes_news_dimension(sample_articles, mock_provider_factory):
    """news_provider + sentiment 주입 시 종합 점수에 뉴스가 반영된다."""
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    close = pd.Series(range(100, 350), index=dates, name="Close")
    price_provider = mock_provider_factory(
        close, {"trailingPE": 18.0, "returnOnEquity": 0.2}
    )

    # 티커 "AI"로 검색되도록 mock 기사 사용
    result = StockAnalyzer(
        "AI",
        provider=price_provider,
        news_provider=MockNewsProvider(sample_articles),
        sentiment=LexiconSentimentAnalyzer(),
    ).analyze()

    assert result.news_score is not None
    assert isinstance(result.recommendation, Recommendation)
    # NEWS 신호가 포함되어야 한다
    assert any(s.name == "NEWS" for s in result.signals)


def test_stock_analyzer_without_news_has_none(mock_provider_factory):
    """뉴스 provider가 없으면 news_score는 None, 기존 2차원 동작 유지."""
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    close = pd.Series(range(100, 350), index=dates, name="Close")
    provider = mock_provider_factory(close, {"trailingPE": 18.0})

    result = StockAnalyzer("TEST", provider=provider).analyze()
    assert result.news_score is None
    assert not any(s.name == "NEWS" for s in result.signals)
