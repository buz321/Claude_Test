"""감성 분석기(SentimentAnalyzer) 추상 인터페이스와 결과 구조."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


def score_to_label(score: float) -> str:
    """-1~+1 점수를 긍정/부정/중립 라벨로 변환한다."""
    if score >= 0.15:
        return "positive"
    if score <= -0.15:
        return "negative"
    return "neutral"


@dataclass
class SentimentResult:
    """텍스트 한 건의 감성 분석 결과.

    Attributes:
        score: -1.0(매우 부정) ~ +1.0(매우 긍정) 범위 점수.
        label: 'positive' / 'negative' / 'neutral'.
        rationale: 점수 근거 설명.
    """

    score: float
    label: str
    rationale: str = ""


class SentimentAnalyzer(ABC):
    """텍스트의 시장 관점 감성을 분석하는 추상 클래스."""

    @abstractmethod
    def analyze(self, text: str) -> SentimentResult:
        """단일 텍스트의 감성을 분석한다."""

    def analyze_many(self, texts: list[str]) -> list[SentimentResult]:
        """여러 텍스트를 분석한다. 기본 구현은 순차 호출."""
        return [self.analyze(t) for t in texts]

    def summarize_market_impact(
        self, topic: str, texts: list[str], results: list[SentimentResult]
    ) -> str:
        """기사 묶음의 시장 영향을 서술형으로 요약한다.

        기본 구현은 집계 통계 기반의 템플릿 요약을 만든다.
        LLM 기반 분석기는 이 메서드를 오버라이드해 더 풍부한 서술을 제공한다.
        """
        if not results:
            return f"'{topic}' 관련 뉴스가 없어 시장 영향을 판단할 수 없습니다."

        pos = sum(1 for r in results if r.label == "positive")
        neg = sum(1 for r in results if r.label == "negative")
        neu = len(results) - pos - neg
        avg = sum(r.score for r in results) / len(results)
        tone = score_to_label(avg)
        tone_kr = {"positive": "긍정적", "negative": "부정적", "neutral": "중립적"}[tone]

        return (
            f"'{topic}' 관련 기사 {len(results)}건 분석: "
            f"긍정 {pos}, 부정 {neg}, 중립 {neu}. "
            f"전반적으로 {tone_kr}(평균 점수 {avg:+.2f})이며, "
            f"단기적으로 관련 종목에 {tone_kr} 영향을 줄 가능성이 있습니다."
        )
