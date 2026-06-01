# stock-analyzer

미국 주식을 위한 **기술적 분석 + 기본적 분석 + 종합 점수/추천** Python 라이브러리입니다.
다른 프로젝트(CLI, 웹 대시보드 등)에서 `import` 해서 재사용할 수 있도록 모듈식으로 설계되었습니다.

## 특징

- **기술적 분석**: 이동평균(SMA/EMA), RSI, MACD, 볼린저 밴드 → 매수/매도 신호
- **기본적 분석**: PER, PBR, ROE, 부채비율, 순이익률 → 가치 점수
- **종합 점수**: 기술적·기본적 점수를 가중합해 `STRONG_BUY` ~ `STRONG_SELL` 추천 + 근거 제공
- **데이터 계층 분리**: `DataProvider` 인터페이스로 데이터 소스를 교체/주입 가능 (테스트 용이)
- **최소 의존성**: `pandas`, `numpy`, `yfinance`

## 설치

```bash
pip install -e .
# 개발/테스트 도구 포함
pip install -e ".[dev]"
```

## 사용법

```python
from stock_analyzer import StockAnalyzer

result = StockAnalyzer("AAPL").analyze()

print(result.recommendation)    # Recommendation.BUY
print(result.composite_score)   # 0.34
print(result.technical_score)   # 0.50
print(result.fundamental_score) # 0.18
print(result.summary())         # 사람이 읽기 좋은 요약
```

기술적/기본적 가중치를 조정하려면:

```python
# 기술적 분석에 70% 가중
StockAnalyzer("TSLA", technical_weight=0.7).analyze()
```

### 데이터 소스 주입 (테스트/오프라인)

```python
from stock_analyzer import StockAnalyzer
from stock_analyzer.data import DataProvider
import pandas as pd

class MyProvider(DataProvider):
    def get_price_history(self, ticker, period="1y"):
        return pd.DataFrame({"Close": [...]})
    def get_fundamentals(self, ticker):
        return {"trailingPE": 18.0, "returnOnEquity": 0.2}

result = StockAnalyzer("AAPL", provider=MyProvider()).analyze()
```

## 프로젝트 구조

```
stock_analyzer/
  models.py            # AnalysisResult, Signal, Recommendation
  data/                # DataProvider 인터페이스 + yfinance 구현
  technical/           # 지표 계산(indicators) + 신호 해석(signals)
  fundamental/         # 재무 지표 추출(metrics) + 점수화(scoring)
  scoring/             # 종합 점수(composite)
  analyzer.py          # StockAnalyzer 파사드
tests/                 # fixture 기반 단위 테스트 (네트워크 불필요)
examples/              # 사용 예시
```

## 테스트

```bash
pytest
```

테스트는 고정된 샘플 데이터(fixture)로 동작하므로 네트워크 없이 실행됩니다.

## 면책 조항

이 라이브러리는 **교육/연구 목적**이며, 산출되는 점수와 추천은 투자 조언이 아닙니다.
실제 투자 결정에 대한 책임은 사용자 본인에게 있습니다.

## 향후 확장 아이디어

- CLI 래퍼 / Streamlit 대시보드
- 백테스팅, 포트폴리오 분석
- 한국 주식 등 다른 시장 지원
