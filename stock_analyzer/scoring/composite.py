"""기술적/기본적 신호를 묶어 종합 점수와 추천을 산출한다."""

from __future__ import annotations

from ..models import Recommendation, Signal


def average_score(signals: list[Signal]) -> float:
    """신호 점수의 단순 평균. 신호가 없으면 0.0(중립)."""
    if not signals:
        return 0.0
    return sum(signal.score for signal in signals) / len(signals)


def composite_score(
    technical_score: float,
    fundamental_score: float,
    technical_weight: float = 0.5,
) -> float:
    """기술적/기본적 점수를 가중합한다.

    Args:
        technical_score: 기술적 분석 점수 (-1.0 ~ +1.0).
        fundamental_score: 기본적 분석 점수 (-1.0 ~ +1.0).
        technical_weight: 기술적 점수에 부여할 가중치 (0.0 ~ 1.0).
            기본적 점수의 가중치는 (1 - technical_weight)로 계산된다.

    Returns:
        가중합된 종합 점수 (-1.0 ~ +1.0).
    """
    if not 0.0 <= technical_weight <= 1.0:
        raise ValueError("technical_weight는 0.0 ~ 1.0 사이여야 합니다.")
    fundamental_weight = 1.0 - technical_weight
    return technical_score * technical_weight + fundamental_score * fundamental_weight


def recommend(score: float) -> Recommendation:
    """종합 점수를 추천 등급으로 변환한다."""
    return Recommendation.from_score(score)
