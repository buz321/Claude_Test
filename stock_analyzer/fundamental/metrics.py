"""재무 데이터에서 핵심 지표를 추출/정규화한다.

yfinance의 `.info`는 일부 값이 누락되거나 None일 수 있으므로
안전하게 float | None 으로 변환한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FundamentalMetrics:
    """기본적 분석에 사용하는 핵심 재무 지표.

    값이 없는 항목은 None으로 둔다.
    """

    pe_ratio: float | None = None  # 주가수익비율 (trailingPE)
    pb_ratio: float | None = None  # 주가순자산비율 (priceToBook)
    roe: float | None = None  # 자기자본이익률 (returnOnEquity)
    debt_to_equity: float | None = None  # 부채비율 (debtToEquity)
    profit_margin: float | None = None  # 순이익률 (profitMargins)


def _to_float(value: object) -> float | None:
    """숫자로 변환 가능하면 float, 아니면 None을 반환한다."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    # NaN 방어
    if result != result:
        return None
    return result


def extract_metrics(fundamentals: dict) -> FundamentalMetrics:
    """yfinance 스타일 재무 딕셔너리에서 FundamentalMetrics를 만든다."""
    return FundamentalMetrics(
        pe_ratio=_to_float(fundamentals.get("trailingPE")),
        pb_ratio=_to_float(fundamentals.get("priceToBook")),
        roe=_to_float(fundamentals.get("returnOnEquity")),
        debt_to_equity=_to_float(fundamentals.get("debtToEquity")),
        profit_margin=_to_float(fundamentals.get("profitMargins")),
    )
