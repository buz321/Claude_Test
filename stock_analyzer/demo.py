"""데모용 결정론적 데이터 제공자.

네트워크 없이 CLI/예시를 돌려볼 수 있도록 티커별로 일관된 가짜 시세·재무·뉴스를
생성한다. 같은 티커는 항상 같은 결과를 내도록 티커 문자열로 RNG를 시드한다.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .data import DataProvider
from .news import MockNewsProvider, NewsArticle


def _seed_for(ticker: str) -> int:
    """티커 문자열을 결정론적 정수 시드로 변환한다."""
    digest = hashlib.sha256(ticker.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


class DemoDataProvider(DataProvider):
    """티커별로 일관된 가짜 시세/재무 데이터를 생성하는 제공자."""

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        rng = np.random.default_rng(_seed_for(ticker))
        n = 250
        dates = pd.date_range(end=datetime.today(), periods=n, freq="B")
        # 티커별로 다른 추세(상승/하락/횡보)와 변동성을 부여한다.
        drift = rng.uniform(-0.4, 0.6)
        start = rng.uniform(80, 300)
        trend = np.linspace(0, drift * start, n)
        noise = np.cumsum(rng.normal(0, start * 0.01, n))
        close = np.maximum(start + trend + noise, 1.0)
        return pd.DataFrame({"Close": close}, index=dates)

    def get_fundamentals(self, ticker: str) -> dict:
        rng = np.random.default_rng(_seed_for(ticker) + 1)
        return {
            "trailingPE": round(rng.uniform(8, 45), 1),
            "priceToBook": round(rng.uniform(0.7, 8.0), 2),
            "returnOnEquity": round(rng.uniform(-0.05, 0.30), 3),
            "debtToEquity": round(rng.uniform(20, 250), 0),
            "profitMargins": round(rng.uniform(-0.1, 0.30), 3),
        }


_POSITIVE_TEMPLATES = [
    "{t} surges as quarterly profits beat estimates with record growth",
    "Analysts upgrade {t} on strong outlook and expansion plans",
    "{t} unveils breakthrough product, shares rally on optimism",
]
_NEGATIVE_TEMPLATES = [
    "{t} faces lawsuit and regulatory probe, shares plunge on concerns",
    "{t} misses earnings; analysts warn of weak demand and losses",
    "{t} announces layoffs amid declining margins and rising debt",
]
_NEUTRAL_TEMPLATES = [
    "{t} schedules annual shareholder meeting for next month",
    "{t} releases new model; market reaction remains muted",
]


def demo_news_provider(query: str) -> MockNewsProvider:
    """질의어를 포함하는 가짜 기사 묶음을 가진 MockNewsProvider를 만든다."""
    rng = np.random.default_rng(_seed_for(query) + 2)
    base = datetime.today()
    templates = _POSITIVE_TEMPLATES + _NEGATIVE_TEMPLATES + _NEUTRAL_TEMPLATES
    articles: list[NewsArticle] = []
    for i, tmpl in enumerate(templates):
        # 질의어가 본문에 포함되도록 한다.
        title = tmpl.format(t=query)
        articles.append(
            NewsArticle(
                title=title,
                summary=f"{query} 관련 시장 동향 보도.",
                source="DemoWire",
                published_at=base - timedelta(hours=i),
            )
        )
    rng.shuffle(articles)
    return MockNewsProvider(articles)
