"""구체적인 뉴스 제공자 구현."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

from .base import NewsArticle, NewsProvider


class MockNewsProvider(NewsProvider):
    """미리 주입한 기사 목록을 반환하는 테스트/오프라인용 제공자.

    query를 제목/요약에 포함하는지로 간단히 필터링하고,
    since가 주어지면 그 이후 기사만 반환한다.
    """

    def __init__(self, articles: list[NewsArticle]) -> None:
        self._articles = list(articles)

    def get_news(
        self,
        query: str,
        *,
        limit: int = 20,
        since: date | None = None,
    ) -> list[NewsArticle]:
        q = query.lower()
        results = [
            a
            for a in self._articles
            if q in a.text.lower()
        ]
        if since is not None:
            results = [
                a
                for a in results
                if a.published_at is not None
                and a.published_at.date() >= since
            ]
        results.sort(
            key=lambda a: a.published_at or datetime.min, reverse=True
        )
        return results[:limit]


class NewsApiProvider(NewsProvider):
    """newsapi.org 의 /v2/everything 엔드포인트를 사용하는 제공자.

    API 키는 생성자 인자 또는 환경변수 NEWSAPI_KEY 에서 읽는다.
    외부 의존성을 늘리지 않기 위해 표준 라이브러리 urllib만 사용한다.
    (실행 시 newsapi.org 로의 네트워크 접근이 필요하다.)
    """

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str | None = None, *, language: str = "en") -> None:
        self.api_key = api_key or os.environ.get("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError(
                "NewsAPI 키가 필요합니다. 인자로 넘기거나 NEWSAPI_KEY 환경변수를 설정하세요."
            )
        self.language = language

    def get_news(
        self,
        query: str,
        *,
        limit: int = 20,
        since: date | None = None,
    ) -> list[NewsArticle]:
        params = {
            "q": query,
            "language": self.language,
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
            "apiKey": self.api_key,
        }
        if since is not None:
            params["from"] = since.isoformat()

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "stock-analyzer"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        if payload.get("status") != "ok":
            raise RuntimeError(f"NewsAPI 오류: {payload.get('message', payload)}")

        articles: list[NewsArticle] = []
        for item in payload.get("articles", [])[:limit]:
            articles.append(
                NewsArticle(
                    title=item.get("title") or "",
                    summary=item.get("description") or "",
                    source=(item.get("source") or {}).get("name", ""),
                    url=item.get("url") or "",
                    published_at=_parse_iso(item.get("publishedAt")),
                )
            )
        return articles


def _parse_iso(value: str | None) -> datetime | None:
    """ISO8601 문자열을 datetime으로 변환한다 (실패 시 None)."""
    if not value:
        return None
    try:
        # NewsAPI는 보통 '2024-01-01T12:34:56Z' 형식을 준다.
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None
