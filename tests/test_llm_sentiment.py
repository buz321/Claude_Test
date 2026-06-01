"""Claude API 기반 감성 분석기 검증 (가짜 클라이언트 주입, 네트워크 불필요).

실제 API를 호출하지 않고, 요청이 올바르게 구성되는지와 응답 파싱이
정확한지를 가짜 클라이언트로 검증한다.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from stock_analyzer.sentiment import ClaudeSentimentAnalyzer


class _FakeMessages:
    def __init__(self, recorder: dict):
        self._recorder = recorder

    def create(self, **kwargs):
        self._recorder["last_kwargs"] = kwargs
        # 구조화 출력 요청이면 results 배열을 담은 JSON을 돌려준다.
        if "output_config" in kwargs:
            payload = {
                "results": [
                    {"score": 0.8, "label": "positive", "rationale": "강세 호재"},
                    {"score": -0.6, "label": "negative", "rationale": "악재"},
                ]
            }
            text = json.dumps(payload)
        else:
            text = "종합적으로 단기 시장에 긍정적 영향이 예상됩니다."
        block = SimpleNamespace(type="text", text=text)
        return SimpleNamespace(content=[block])


class _FakeClient:
    def __init__(self):
        self.recorder: dict = {}
        self.messages = _FakeMessages(self.recorder)


def test_analyze_many_parses_results():
    client = _FakeClient()
    analyzer = ClaudeSentimentAnalyzer(client=client)

    results = analyzer.analyze_many(["good news", "bad news"])
    assert len(results) == 2
    assert results[0].score == 0.8 and results[0].label == "positive"
    assert results[1].score == -0.6 and results[1].label == "negative"


def test_request_uses_structured_output_and_caching():
    client = _FakeClient()
    analyzer = ClaudeSentimentAnalyzer(client=client)
    analyzer.analyze("some headline")

    kwargs = client.recorder["last_kwargs"]
    assert kwargs["model"] == "claude-opus-4-8"
    # 구조화 출력 스키마가 지정되어야 한다
    assert kwargs["output_config"]["format"]["type"] == "json_schema"
    # 시스템 프롬프트에 prompt caching이 걸려 있어야 한다
    assert kwargs["system"][0]["cache_control"]["type"] == "ephemeral"


def test_summarize_market_impact_returns_text():
    client = _FakeClient()
    analyzer = ClaudeSentimentAnalyzer(client=client)
    results = analyzer.analyze_many(["a", "b"])
    summary = analyzer.summarize_market_impact("AI", ["a", "b"], results)
    assert "긍정적" in summary or summary  # 텍스트가 반환됨
