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
        composite_score: 기술적/기본적/뉴스 점수를 가중합한 최종 점수 (-1.0 ~ +1.0).
        technical_score: 기술적 분석 점수 (-1.0 ~ +1.0).
        fundamental_score: 기본적 분석 점수 (-1.0 ~ +1.0).
        news_score: 뉴스 감성 점수 (-1.0 ~ +1.0). 뉴스 분석을 안 했으면 None.
        signals: 분석에 사용된 모든 개별 신호.
        reasons: 추천 근거 요약 문자열 목록.
    """

    ticker: str
    recommendation: Recommendation
    composite_score: float
    technical_score: float
    fundamental_score: float
    news_score: float | None = None
    signals: list[Signal] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """결과를 한눈에 보기 좋은 문자열로 반환한다."""
        lines = [
            f"[{self.ticker}] 추천: {self.recommendation.value} "
            f"(종합 점수 {self.composite_score:+.2f})",
            f"  - 기술적 점수: {self.technical_score:+.2f}",
            f"  - 기본적 점수: {self.fundamental_score:+.2f}",
        ]
        if self.news_score is not None:
            lines.append(f"  - 뉴스 점수: {self.news_score:+.2f}")
        lines.append("  근거:")
        lines.extend(f"    · {reason}" for reason in self.reasons)
        return "\n".join(lines)


@dataclass
class PortfolioResult:
    """여러 종목을 분석해 종합 점수로 순위를 매긴 결과.

    Attributes:
        results: 종합 점수 내림차순으로 정렬된 종목별 분석 결과.
        errors: 분석에 실패한 종목 → 오류 메시지.
    """

    results: list["AnalysisResult"] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def average_score(self) -> float:
        """포트폴리오 전체의 평균 종합 점수."""
        if not self.results:
            return 0.0
        return sum(r.composite_score for r in self.results) / len(self.results)

    @property
    def best(self) -> "AnalysisResult | None":
        return self.results[0] if self.results else None

    @property
    def worst(self) -> "AnalysisResult | None":
        return self.results[-1] if self.results else None

    def summary(self) -> str:
        """순위표 형태의 문자열로 반환한다."""
        lines = [
            f"=== 포트폴리오 분석 ({len(self.results)}개 종목) ===",
            f"평균 종합 점수: {self.average_score:+.2f}",
            "",
            f"{'순위':<4}{'티커':<8}{'추천':<13}{'종합':>7}{'기술':>7}{'기본':>7}{'뉴스':>7}",
        ]
        for i, r in enumerate(self.results, 1):
            news = f"{r.news_score:+.2f}" if r.news_score is not None else "  -  "
            lines.append(
                f"{i:<4}{r.ticker:<8}{r.recommendation.value:<13}"
                f"{r.composite_score:>+7.2f}{r.technical_score:>+7.2f}"
                f"{r.fundamental_score:>+7.2f}{news:>7}"
            )
        if self.errors:
            lines.append("")
            lines.append("분석 실패:")
            lines.extend(f"  · {t}: {msg}" for t, msg in self.errors.items())
        return "\n".join(lines)


@dataclass
class NewsDigest:
    """특정 토픽에 대한 뉴스 종합 분석 결과 (기능 1·2).

    Attributes:
        topic: 검색 토픽 (예: "AI").
        article_count: 분석한 기사 수.
        overall_score: 전체 평균 감성 점수 (-1.0 ~ +1.0).
        overall_label: 전체 감성 라벨 (positive/negative/neutral).
        market_impact: 시장 영향 서술형 요약.
        headlines: (제목, 감성점수, 라벨) 튜플 목록.
    """

    topic: str
    article_count: int
    overall_score: float
    overall_label: str
    market_impact: str
    headlines: list[tuple[str, float, str]] = field(default_factory=list)

    def summary(self) -> str:
        """다이제스트를 보기 좋은 문자열로 반환한다."""
        lines = [
            f"=== '{self.topic}' 뉴스 다이제스트 (기사 {self.article_count}건) ===",
            f"전체 감성: {self.overall_label} ({self.overall_score:+.2f})",
            "",
            f"[시장 영향] {self.market_impact}",
            "",
            "주요 헤드라인:",
        ]
        for title, score, label in self.headlines:
            lines.append(f"  · ({score:+.2f} {label}) {title}")
        return "\n".join(lines)
