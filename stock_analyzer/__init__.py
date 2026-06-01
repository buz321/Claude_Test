"""stock_analyzer: 미국 주식 기술적/기본적/뉴스/종합 점수 분석 라이브러리."""

from .analyzer import StockAnalyzer
from .data import DataProvider, YFinanceProvider
from .models import (
    AnalysisResult,
    NewsDigest,
    PortfolioResult,
    Recommendation,
    Signal,
)
from .news_analyzer import NewsAnalyzer
from .portfolio import PortfolioAnalyzer

__version__ = "0.3.0"

__all__ = [
    "StockAnalyzer",
    "NewsAnalyzer",
    "PortfolioAnalyzer",
    "AnalysisResult",
    "NewsDigest",
    "PortfolioResult",
    "Recommendation",
    "Signal",
    "DataProvider",
    "YFinanceProvider",
]
