"""사전(키워드) 기반 감성 분석기.

금융 뉴스에서 자주 쓰이는 강세/약세 단어 사전을 이용해
외부 의존성·네트워크 없이 감성 점수를 계산한다.
"""

from __future__ import annotations

import re

from .base import SentimentAnalyzer, SentimentResult, score_to_label

# 강세(긍정) 신호 단어
_BULLISH = {
    "surge", "soar", "rally", "gain", "gains", "jump", "jumps", "rise", "rises",
    "beat", "beats", "record", "growth", "grow", "profit", "profits", "upgrade",
    "outperform", "bullish", "boom", "strong", "strength", "breakthrough",
    "expansion", "optimistic", "positive", "boost", "boosts", "win", "wins",
    "高", "상승", "급등", "호재", "최대", "성장", "흑자", "돌파",
}

# 약세(부정) 신호 단어
_BEARISH = {
    "plunge", "plummet", "slump", "fall", "falls", "drop", "drops", "decline",
    "miss", "misses", "loss", "losses", "downgrade", "underperform", "bearish",
    "crash", "weak", "weakness", "cut", "cuts", "lawsuit", "probe", "recall",
    "warning", "warn", "warns", "layoff", "layoffs", "bankruptcy", "fraud",
    "negative", "concern", "concerns", "risk", "risks", "selloff",
    "하락", "급락", "악재", "적자", "감원", "소송", "리콜", "우려",
}

_WORD_RE = re.compile(r"[A-Za-z가-힣]+")


class LexiconSentimentAnalyzer(SentimentAnalyzer):
    """강세/약세 단어 빈도로 감성을 점수화하는 분석기."""

    def analyze(self, text: str) -> SentimentResult:
        tokens = [t.lower() for t in _WORD_RE.findall(text)]
        # 한글은 .lower()의 영향이 없고, 영문은 소문자로 매칭.
        pos = sum(1 for t in tokens if t in _BULLISH)
        neg = sum(1 for t in tokens if t in _BEARISH)

        total = pos + neg
        if total == 0:
            return SentimentResult(0.0, "neutral", "강세/약세 키워드 없음 → 중립")

        score = (pos - neg) / total
        label = score_to_label(score)
        rationale = f"강세 단어 {pos}개, 약세 단어 {neg}개 → {label}"
        return SentimentResult(score, label, rationale)
