"""분석 결과를 표현하는 데이터 구조 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Recommendation(str, Enum):
    """최종 투자 추천 등급. 종합 점수를 사람이 읽기 쉬운 등급으로 변환한 값."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

    @classmethod
    def from_score(cls, score: float) -> "Recommendation":
        """-1.0 ~ +1.0 범위의 점수를 추천 등급으로 변환한다.

        +1에 가까울수록 강한 매수, -1에 가까울수록 강한 매도 신호.
        """
        if score >= 0.5:
            return cls.STRONG_BUY
        if score >= 0.15:
            return cls.BUY
        if score <= -0.5:
            return cls.STRONG_SELL
        if score <= -0.15:
            return cls.SELL
        return cls.HOLD


@dataclass
class Signal:
    """개별 지표가 만들어낸 단일 신호.

    Attributes:
        name: 신호를 생성한 지표 이름 (예: "RSI", "MACD").
        score: -1.0(강한 매도) ~ +1.0(강한 매수) 범위의 신호 강도.
        reason: 사람이 읽을 수 있는 근거 설명.
    """

    name: str
    score: float
    reason: str


@dataclass
class AnalysisResult:
    """한 종목에 대한 전체 분석 결과.

    Attributes:
        ticker: 분석 대상 티커 (예: "AAPL").
        recommendation: 최종 추천 등급.
        composite_score: 기술적/기본적 점수를 가중합한 최종 점수 (-1.0 ~ +1.0).
        technical_score: 기술적 분석 점수 (-1.0 ~ +1.0).
        fundamental_score: 기본적 분석 점수 (-1.0 ~ +1.0).
        signals: 분석에 사용된 모든 개별 신호.
        reasons: 추천 근거 요약 문자열 목록.
    """

    ticker: str
    recommendation: Recommendation
    composite_score: float
    technical_score: float
    fundamental_score: float
    signals: list[Signal] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """결과를 한눈에 보기 좋은 문자열로 반환한다."""
        lines = [
            f"[{self.ticker}] 추천: {self.recommendation.value} "
            f"(종합 점수 {self.composite_score:+.2f})",
            f"  - 기술적 점수: {self.technical_score:+.2f}",
            f"  - 기본적 점수: {self.fundamental_score:+.2f}",
            "  근거:",
        ]
        lines.extend(f"    · {reason}" for reason in self.reasons)
        return "\n".join(lines)
