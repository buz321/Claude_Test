# stock-analyzer

미국 주식을 위한 **기술적 분석 + 기본적 분석 + 뉴스 감성 + 종합 점수/추천** Python 라이브러리입니다.
다른 프로젝트(CLI, 웹 대시보드 등)에서 `import` 해서 재사용할 수 있도록 모듈식으로 설계되었습니다.

## 특징

- **기술적 분석**: 이동평균(SMA/EMA), RSI, MACD, 볼린저 밴드 → 매수/매도 신호
- **기본적 분석**: PER, PBR, ROE, 부채비율, 순이익률 → 가치 점수
- **뉴스 감성 분석**: 토픽(예: "AI") 뉴스 수집 → 감성 점수 + 시장 영향 요약
  - 사전 기반(오프라인) 또는 Claude API 기반(LLM) 선택 가능
- **종합 점수**: 기술적·기본적·뉴스 점수를 가중합해 `STRONG_BUY` ~ `STRONG_SELL` 추천 + 근거 제공
- **차트 시각화**: 가격+이동평균+볼린저밴드 / RSI / MACD 3단 차트 (matplotlib, 선택적)
- **계층 분리**: `DataProvider` / `NewsProvider` / `SentimentAnalyzer` 인터페이스로
  데이터 소스와 분석 엔진을 자유롭게 교체/주입 (테스트 용이)
- **최소 의존성**: `pandas`, `numpy`, `yfinance` (+ 시각화 `matplotlib`, + LLM `anthropic`)

## 설치

```bash
pip install -e .
# 차트 시각화 포함
pip install -e ".[viz]"
# Claude API 기반 뉴스 감성 분석 포함
pip install -e ".[llm]"
# 개발/테스트 도구 포함
pip install -e ".[dev]"
```

## CLI 사용법

설치하면 `stock-analyzer` 명령(또는 `python -m stock_analyzer`)을 쓸 수 있습니다.

```bash
# 종목 분석
stock-analyzer analyze AAPL
stock-analyzer analyze NVDA --news            # 뉴스 감성까지 반영
stock-analyzer analyze NVDA --news --llm      # 뉴스 감성에 Claude API 사용

# 토픽 뉴스 다이제스트
stock-analyzer news AI --limit 20 --days 1

# 포트폴리오: 여러 종목 비교·랭킹
stock-analyzer portfolio AAPL MSFT NVDA TSLA GOOGL
stock-analyzer portfolio AAPL NVDA --news     # 뉴스까지 반영

# 차트 저장
stock-analyzer chart AAPL --out aapl.png

# JSON 출력
stock-analyzer analyze AAPL --json
```

> 💡 **`--demo` 플래그**: 네트워크 없이 내장 가짜 데이터로 동작을 확인할 수 있습니다.
> `stock-analyzer analyze AAPL --demo --news` 처럼 쓰면 키/네트워크 없이 전체 흐름을 볼 수 있어요.
> 실데이터는 `yfinance`(시세)·`NewsAPI`(뉴스)·`Anthropic API`(LLM 감성) 접근이 필요합니다.

## 라이브러리 사용법

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

### 차트 시각화

```python
from stock_analyzer import StockAnalyzer

# 분석 + 차트를 한 번에. PNG로 저장.
result, fig = StockAnalyzer("AAPL").plot(save_path="aapl.png")
```

차트는 가격/이동평균/볼린저밴드(1단), RSI(2단), MACD(3단)를 보여주며
제목에 추천 등급과 종합 점수가 표시됩니다. `matplotlib`의 `Agg` 백엔드를 써서
서버/헤드리스 환경에서도 PNG 저장이 가능합니다.

### 뉴스 감성 분석 (토픽 다이제스트)

토픽으로 그날의 뉴스를 모아 감성과 시장 영향을 분석합니다.

```python
from datetime import date
from stock_analyzer import NewsAnalyzer
from stock_analyzer.news import NewsApiProvider          # NEWSAPI_KEY 필요
from stock_analyzer.sentiment import ClaudeSentimentAnalyzer  # ANTHROPIC_API_KEY 필요

na = NewsAnalyzer(provider=NewsApiProvider(), sentiment=ClaudeSentimentAnalyzer())
digest = na.digest("AI", limit=20, since=date.today())
print(digest.summary())   # 전체 감성 + 시장 영향 요약 + 헤드라인별 점수
```

오프라인/무료로 쓰려면 사전 기반 분석기를 사용합니다 (네트워크·키 불필요):

```python
from stock_analyzer.sentiment import LexiconSentimentAnalyzer
from stock_analyzer.news import MockNewsProvider

na = NewsAnalyzer(provider=MockNewsProvider(articles), sentiment=LexiconSentimentAnalyzer())
```

### 뉴스를 반영한 종목 등락 분석

종목 분석에 뉴스 감성을 세 번째 차원으로 합쳐 등락 방향을 판단합니다.

```python
from stock_analyzer import StockAnalyzer
from stock_analyzer.news import NewsApiProvider
from stock_analyzer.sentiment import ClaudeSentimentAnalyzer

result = StockAnalyzer(
    "NVDA",
    news_provider=NewsApiProvider(),
    sentiment=ClaudeSentimentAnalyzer(),
).analyze()
print(result.news_score)       # 뉴스 감성 점수
print(result.recommendation)   # 기술+기본+뉴스 종합 추천
```

기본 가중치는 기술 0.4 / 기본 0.4 / 뉴스 0.2이며 `weights` 인자로 조정할 수 있습니다.
뉴스 provider를 주입하지 않으면 기존 2차원(기술+기본) 분석으로 동작합니다.

### 포트폴리오 분석 (여러 종목 랭킹)

```python
from stock_analyzer import PortfolioAnalyzer

result = PortfolioAnalyzer().analyze(["AAPL", "MSFT", "NVDA", "TSLA"])
print(result.summary())     # 종합 점수 순 순위표
print(result.best.ticker)   # 최상위 종목
print(result.average_score) # 포트폴리오 평균 점수
```

개별 종목 분석이 실패해도 나머지는 계속 진행되며, 실패 종목은 `result.errors`에 기록됩니다.

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
  models.py            # AnalysisResult, NewsDigest, Signal, Recommendation
  data/                # DataProvider 인터페이스 + yfinance 구현
  technical/           # 지표 계산(indicators) + 신호 해석(signals)
  fundamental/         # 재무 지표 추출(metrics) + 점수화(scoring)
  news/                # NewsProvider 인터페이스 + Mock/NewsAPI 구현
  sentiment/           # SentimentAnalyzer + 사전 기반(lexicon) + Claude API(llm)
  scoring/             # 종합 점수(composite, weighted_score)
  analyzer.py          # StockAnalyzer 파사드 (기술+기본+뉴스)
  news_analyzer.py     # NewsAnalyzer 파사드 (토픽 다이제스트)
  portfolio.py         # PortfolioAnalyzer 파사드 (여러 종목 랭킹)
  cli.py / __main__.py # CLI (analyze/news/portfolio/chart)
  demo.py              # 오프라인 데모용 결정론적 데이터 제공자
  viz/                 # matplotlib 차트
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

- Streamlit 인터랙티브 대시보드
- 백테스팅, 포트폴리오 비중 최적화
- 한국 주식 등 다른 시장 지원
- 뉴스 소스 확장(Finnhub, RSS), 종목별 뉴스 캐싱

## 참고: 원격 실행 환경에서의 실데이터

Claude Code on the web 같은 원격 환경은 네트워크 allowlist 정책에 따라
야후 파이낸스 / NewsAPI / Anthropic API 접근이 막힐 수 있습니다
(`HTTP 403: Host not in allowlist`). 이 경우 실시간 시세·뉴스·LLM 분석은
로컬 PC에서 실행하거나, 환경의 네트워크 정책을 개방형으로 설정해야 합니다.
단위 테스트와 mock/사전 기반 데모·시각화는 네트워크 없이 동작합니다.
