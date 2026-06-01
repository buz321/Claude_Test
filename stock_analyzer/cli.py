"""stock-analyzer 명령줄 인터페이스.

표준 argparse만 사용하며 세 가지 서브커맨드를 제공한다:

    stock-analyzer analyze AAPL              # 종목 분석
    stock-analyzer analyze NVDA --news       # 뉴스까지 반영
    stock-analyzer news AI                    # 토픽 뉴스 다이제스트
    stock-analyzer chart AAPL --out aapl.png # 차트 저장

실데이터는 네트워크(yfinance/NewsAPI)와 API 키가 필요하다.
네트워크가 막힌 환경에서는 --demo 플래그로 내장 가짜 데이터를 사용해 동작을 확인할 수 있다.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta

from . import __version__


def _make_price_provider(demo: bool):
    if demo:
        from .demo import DemoDataProvider

        return DemoDataProvider()
    from .data import YFinanceProvider

    return YFinanceProvider()


def _make_sentiment(use_llm: bool):
    if use_llm:
        from .sentiment import ClaudeSentimentAnalyzer

        return ClaudeSentimentAnalyzer()
    from .sentiment import LexiconSentimentAnalyzer

    return LexiconSentimentAnalyzer()


def _make_news_provider(demo: bool, query: str):
    if demo:
        from .demo import demo_news_provider

        return demo_news_provider(query)
    from .news import NewsApiProvider

    return NewsApiProvider()


def cmd_analyze(args: argparse.Namespace) -> int:
    from .analyzer import StockAnalyzer

    provider = _make_price_provider(args.demo)
    news_provider = None
    sentiment = None
    if args.news:
        news_provider = _make_news_provider(args.demo, args.ticker)
        sentiment = _make_sentiment(args.llm)

    analyzer = StockAnalyzer(
        args.ticker,
        provider=provider,
        news_provider=news_provider,
        sentiment=sentiment,
    )
    result = analyzer.analyze(period=args.period)

    if args.plot:
        from .viz import plot_analysis

        history = provider.get_price_history(args.ticker, period=args.period)
        plot_analysis(history["Close"], result, save_path=args.plot)
        print(f"차트 저장: {args.plot}")

    if args.json:
        data = asdict(result)
        data["recommendation"] = result.recommendation.value
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print(result.summary())
    return 0


def cmd_news(args: argparse.Namespace) -> int:
    from .news_analyzer import NewsAnalyzer

    provider = _make_news_provider(args.demo, args.topic)
    sentiment = _make_sentiment(args.llm)
    since = date.today() - timedelta(days=args.days) if args.days else None

    digest = NewsAnalyzer(provider=provider, sentiment=sentiment).digest(
        args.topic, limit=args.limit, since=since
    )

    if args.json:
        data = asdict(digest)
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print(digest.summary())
    return 0


def cmd_chart(args: argparse.Namespace) -> int:
    from .analyzer import StockAnalyzer

    provider = _make_price_provider(args.demo)
    out = args.out or f"{args.ticker.upper()}.png"
    result, _ = StockAnalyzer(args.ticker, provider=provider).plot(
        period=args.period, save_path=out
    )
    print(result.summary())
    print(f"\n차트 저장: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-analyzer",
        description="미국 주식 기술/기본/뉴스 분석 CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # 공통 옵션을 부모 파서로 묶는다.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--demo",
        action="store_true",
        help="네트워크 없이 내장 가짜 데이터 사용 (동작 확인용)",
    )
    common.add_argument("--json", action="store_true", help="JSON으로 출력")

    p_analyze = sub.add_parser(
        "analyze", parents=[common], help="종목을 분석하고 추천을 출력"
    )
    p_analyze.add_argument("ticker", help="티커 (예: AAPL)")
    p_analyze.add_argument("--period", default="1y", help="시세 기간 (기본 1y)")
    p_analyze.add_argument(
        "--news", action="store_true", help="뉴스 감성을 분석에 반영"
    )
    p_analyze.add_argument(
        "--llm",
        action="store_true",
        help="뉴스 감성에 Claude API 사용 (ANTHROPIC_API_KEY 필요)",
    )
    p_analyze.add_argument("--plot", metavar="PATH", help="차트를 PNG로 저장")
    p_analyze.set_defaults(func=cmd_analyze)

    p_news = sub.add_parser(
        "news", parents=[common], help="토픽 뉴스 다이제스트를 출력"
    )
    p_news.add_argument("topic", help="검색 토픽/키워드 (예: AI)")
    p_news.add_argument("--limit", type=int, default=15, help="최대 기사 수 (기본 15)")
    p_news.add_argument(
        "--days", type=int, default=0, help="최근 N일 내 기사만 (기본 0=전체)"
    )
    p_news.add_argument(
        "--llm",
        action="store_true",
        help="감성/시장영향에 Claude API 사용 (ANTHROPIC_API_KEY 필요)",
    )
    p_news.set_defaults(func=cmd_news)

    p_chart = sub.add_parser(
        "chart", parents=[common], help="종목 차트를 PNG로 저장"
    )
    p_chart.add_argument("ticker", help="티커 (예: AAPL)")
    p_chart.add_argument("--period", default="1y", help="시세 기간 (기본 1y)")
    p_chart.add_argument("--out", metavar="PATH", help="저장 경로 (기본 <TICKER>.png)")
    p_chart.set_defaults(func=cmd_chart)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI는 친절한 메시지로 마무리
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
