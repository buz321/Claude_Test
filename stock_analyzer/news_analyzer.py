"""토픽 기반 뉴스 다이제스트 (기능 1·2).

키워드(예: "AI")로 그날의 새 뉴스를 모아 감성을 분석하고
시장 영향을 종합 요약한다.
"""

from __future__ import annotations

from datetime import date

from .models import NewsDigest
from .news import NewsProvider
from .sentiment import LexiconSentimentAnalyzer, SentimentAnalyzer, score_to_label


class NewsAnalyzer:
    """뉴스 수집 + 감성 분석 + 시장 영향 요약을 묶는 파사드.

    예시::

        from stock_analyzer import NewsAnalyzer
        from stock_analyzer.news import NewsApiProvider

        na = NewsAnalyzer(provider=NewsApiProvider())  # 키 필요
        digest = na.digest("AI", limit=20, since=date.today())
        print(digest.summary())

    provider/sentiment를 주입하지 않으면 mock/사전 기반을 직접 넣어야 하므로,
    실제 사용 시에는 NewsApiProvider나 ClaudeSentimentAnalyzer를 주입한다.
    """

    def __init__(
        self,
        provider: NewsProvider,
        sentiment: SentimentAnalyzer | None = None,
    ) -> None:
        self.provider = provider
        self.sentiment = sentiment or LexiconSentimentAnalyzer()

    def digest(
        self,
        topic: str,
        *,
        limit: int = 20,
        since: date | None = None,
    ) -> NewsDigest:
        """토픽에 대한 뉴스 다이제스트를 생성한다."""
        articles = self.provider.get_news(topic, limit=limit, since=since)
        if not articles:
            return NewsDigest(
                topic=topic,
                article_count=0,
                overall_score=0.0,
                overall_label="neutral",
                market_impact=f"'{topic}' 관련 뉴스를 찾지 못했습니다.",
                headlines=[],
            )

        texts = [a.text for a in articles]
        results = self.sentiment.analyze_many(texts)

        overall_score = sum(r.score for r in results) / len(results)
        headlines = [
            (article.title, result.score, result.label)
            for article, result in zip(articles, results)
        ]
        market_impact = self.sentiment.summarize_market_impact(topic, texts, results)

        return NewsDigest(
            topic=topic,
            article_count=len(articles),
            overall_score=overall_score,
            overall_label=score_to_label(overall_score),
            market_impact=market_impact,
            headlines=headlines,
        )
