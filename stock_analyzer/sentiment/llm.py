"""Claude API 기반 감성/시장영향 분석기.

사전 기반 분석기보다 훨씬 정교하게 뉴스의 어조와 시장 함의를 해석한다.
실행하려면 `anthropic` 패키지와 ANTHROPIC_API_KEY(또는 주입한 클라이언트)가 필요하다.

설계 노트:
- 공식 Anthropic SDK 사용. 기본 모델은 claude-opus-4-8.
- 구조화 출력(output_config.format json_schema)으로 파싱 안정성 확보.
- 여러 기사를 한 번의 요청으로 분석(analyze_many)해 토큰/지연을 절약.
- 공유 시스템 프롬프트에 prompt caching을 걸어 반복 호출 비용 절감.
- 테스트를 위해 client를 주입할 수 있다(네트워크 없이 가짜 클라이언트 사용).
"""

from __future__ import annotations

import json

from .base import SentimentAnalyzer, SentimentResult, score_to_label

_SYSTEM_PROMPT = (
    "You are a financial news sentiment analyst. For each news item, judge how it "
    "is likely to affect the related stock or market in the short term. "
    "Score each item from -1.0 (very bearish/negative) to +1.0 (very bullish/positive), "
    "where 0 is neutral. Base the score on market impact, not general tone. "
    "Provide a brief rationale (one sentence) for each."
)

# 여러 기사를 한 번에 분석할 때 사용하는 출력 스키마.
_BATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "score": {"type": "number"},
                    "label": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"],
                    },
                    "rationale": {"type": "string"},
                },
                "required": ["score", "label", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def _clamp(score: float) -> float:
    return max(-1.0, min(1.0, score))


class ClaudeSentimentAnalyzer(SentimentAnalyzer):
    """Claude를 호출해 뉴스 감성과 시장 영향을 분석한다."""

    def __init__(self, model: str = "claude-opus-4-8", client=None) -> None:
        self.model = model
        self._client = client

    @property
    def client(self):
        # anthropic은 무거운 선택적 의존성이므로 실제 사용 시점에 임포트한다.
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def analyze(self, text: str) -> SentimentResult:
        return self.analyze_many([text])[0]

    def analyze_many(self, texts: list[str]) -> list[SentimentResult]:
        if not texts:
            return []

        numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts))
        user_content = (
            f"Analyze the following {len(texts)} news items. "
            "Return one result per item, in the same order.\n\n" + numbered
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            # 분류 작업이라 사고(thinking)는 끄고 빠르게 처리한다.
            thinking={"type": "disabled"},
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    # 반복 호출 시 시스템 프롬프트 프리픽스를 캐시한다.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            output_config={"format": {"type": "json_schema", "schema": _BATCH_SCHEMA}},
            messages=[{"role": "user", "content": user_content}],
        )

        text_block = next(
            (b.text for b in response.content if b.type == "text"), "{}"
        )
        data = json.loads(text_block)
        results = data.get("results", [])

        out: list[SentimentResult] = []
        for i in range(len(texts)):
            if i < len(results):
                item = results[i]
                score = _clamp(float(item.get("score", 0.0)))
                label = item.get("label") or score_to_label(score)
                rationale = item.get("rationale", "")
                out.append(SentimentResult(score, label, rationale))
            else:
                out.append(SentimentResult(0.0, "neutral", "분석 결과 누락"))
        return out

    def summarize_market_impact(
        self, topic: str, texts: list[str], results: list[SentimentResult]
    ) -> str:
        if not results:
            return f"'{topic}' 관련 뉴스가 없어 시장 영향을 판단할 수 없습니다."

        # 개별 점수와 기사 요지를 모아 종합 서술을 요청한다.
        lines = "\n".join(
            f"- ({r.score:+.2f}, {r.label}) {t[:200]}"
            for t, r in zip(texts, results)
        )
        prompt = (
            f"다음은 '{topic}' 관련 뉴스 기사와 개별 감성 점수입니다.\n\n{lines}\n\n"
            "이 뉴스들이 시장과 관련 종목에 단기적으로 어떤 영향을 줄지 "
            "한국어로 3~4문장으로 종합 분석해 주세요. 핵심 테마와 방향성을 포함하세요."
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            # 종합 분석은 약간의 추론이 도움이 되므로 adaptive thinking 사용.
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        return next((b.text for b in response.content if b.type == "text"), "")
