"""뉴스 다이제스트 + 종목 등락 분석 데모.

오프라인 데모(mock)와 실데이터/LLM 사용법을 함께 보여준다.

실행 (오프라인):
    python examples/news_demo.py

실데이터 + Claude 분석 (네트워크 + 키 필요):
    export NEWSAPI_KEY=...        # https://newsapi.org
    export ANTHROPIC_API_KEY=...
    그리고 아래 main()의 '실데이터' 블록 주석을 해제하세요.
"""

from __future__ import annotations

from datetime import datetime

from stock_analyzer import NewsAnalyzer, StockAnalyzer
from stock_analyzer.news import MockNewsProvider, NewsArticle
from stock_analyzer.sentiment import LexiconSentimentAnalyzer


def offline_demo() -> None:
    articles = [
        NewsArticle(
            "NVDA AI chip demand surges, profits beat record estimates",
            "Strong growth and expansion boost the sector.",
            "Wire",
            published_at=datetime(2026, 6, 1, 9),
        ),
        NewsArticle(
            "NVDA faces probe over export concerns, shares drop",
            "Regulatory warnings weigh on the stock.",
            "Wire",
            published_at=datetime(2026, 6, 1, 10),
        ),
        NewsArticle(
            "NVDA unveils breakthrough driving bullish optimism",
            "Analysts upgrade on strong outlook.",
            "Wire",
            published_at=datetime(2026, 6, 1, 11),
        ),
    ]
    provider = MockNewsProvider(articles)
    sentiment = LexiconSentimentAnalyzer()

    # 기능 1·2: 토픽 뉴스 다이제스트 + 시장 영향
    digest = NewsAnalyzer(provider=provider, sentiment=sentiment).digest("NVDA")
    print(digest.summary())
    print()


def realtime_example() -> None:
    """실데이터 + Claude 사용 예시 (네트워크/키 필요 — 기본 비활성)."""
    from stock_analyzer.news import NewsApiProvider
    from stock_analyzer.sentiment import ClaudeSentimentAnalyzer

    na = NewsAnalyzer(
        provider=NewsApiProvider(),  # NEWSAPI_KEY 사용
        sentiment=ClaudeSentimentAnalyzer(),  # ANTHROPIC_API_KEY 사용
    )
    print(na.digest("AI", limit=20).summary())

    # 기능 3: 뉴스를 반영한 종목 등락 분석
    result = StockAnalyzer(
        "NVDA",
        news_provider=NewsApiProvider(),
        sentiment=ClaudeSentimentAnalyzer(),
    ).analyze()
    print(result.summary())


if __name__ == "__main__":
    offline_demo()
    # 실데이터로 보려면 아래 주석을 해제하세요 (네트워크 + API 키 필요):
    # realtime_example()
