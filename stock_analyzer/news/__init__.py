"""뉴스 계층: 제공자 인터페이스와 구현."""

from .base import NewsArticle, NewsProvider
from .providers import MockNewsProvider, NewsApiProvider

__all__ = ["NewsArticle", "NewsProvider", "MockNewsProvider", "NewsApiProvider"]
