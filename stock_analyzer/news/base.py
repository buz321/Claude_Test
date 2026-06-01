"""뉴스 제공자(NewsProvider) 추상 인터페이스와 뉴스 데이터 구조.

시세 데이터와 마찬가지로, 뉴스 소스(NewsAPI, Finnhub, RSS 등)와
분석 로직을 분리한다. 테스트/오프라인에서는 MockNewsProvider를 주입한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class NewsArticle:
    """뉴스 기사 한 건.

    Attributes:
        title: 기사 제목.
        summary: 본문 요약/설명 (없으면 빈 문자열).
        source: 출처 매체명.
        url: 기사 링크.
        published_at: 발행 시각.
    """

    title: str
    summary: str = ""
    source: str = ""
    url: str = ""
    published_at: datetime | None = None

    @property
    def text(self) -> str:
        """감성 분석에 쓸 제목+요약 결합 텍스트."""
        return f"{self.title}. {self.summary}".strip()


class NewsProvider(ABC):
    """뉴스 기사를 제공하는 추상 클래스."""

    @abstractmethod
    def get_news(
        self,
        query: str,
        *,
        limit: int = 20,
        since: date | None = None,
    ) -> list[NewsArticle]:
        """질의어에 해당하는 뉴스 기사 목록을 반환한다.

        Args:
            query: 검색 키워드 (토픽 "AI" 또는 티커 "NVDA" 등).
            limit: 최대 기사 수.
            since: 지정 시 해당 날짜 이후 기사만 반환 (그날의 새 뉴스).

        Returns:
            발행 시각 내림차순(최신 우선) NewsArticle 목록.
        """
