"""감성 분석: 사전 기반(기본) + Claude API 기반(선택)."""

from .base import SentimentAnalyzer, SentimentResult, score_to_label
from .lexicon import LexiconSentimentAnalyzer

__all__ = [
    "SentimentAnalyzer",
    "SentimentResult",
    "score_to_label",
    "LexiconSentimentAnalyzer",
    "ClaudeSentimentAnalyzer",
]


def __getattr__(name: str):
    # ClaudeSentimentAnalyzer는 anthropic 의존성을 끌어오므로 지연 로딩한다.
    if name == "ClaudeSentimentAnalyzer":
        from .llm import ClaudeSentimentAnalyzer

        return ClaudeSentimentAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
