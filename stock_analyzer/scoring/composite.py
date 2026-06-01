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


def weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    """여러 점수를 가중 평균한다.

    components에 존재하는 키만 사용하며, 해당 키의 가중치 합으로 정규화한다.
    예: 뉴스 분석을 안 한 경우 'news'를 빼면 나머지 가중치로 자동 재정규화된다.

    Args:
        components: {"technical": 0.3, "fundamental": -0.1, ...}
        weights: {"technical": 0.4, "fundamental": 0.4, "news": 0.2}

    Returns:
        가중 평균 점수. 유효한 가중치 합이 0이면 0.0.
    """
    total_weight = sum(weights.get(k, 0.0) for k in components)
    if total_weight <= 0:
        return 0.0
    return sum(components[k] * weights.get(k, 0.0) for k in components) / total_weight


def recommend(score: float) -> Recommendation:
    """종합 점수를 추천 등급으로 변환한다."""
    return Recommendation.from_score(score)
