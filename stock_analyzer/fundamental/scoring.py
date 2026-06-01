"""재무 지표를 매수/매도 신호로 점수화한다.

각 지표를 일반적인 기준값과 비교해 -1.0 ~ +1.0 범위의 Signal로 변환한다.
기준값은 미국 시장 대형주를 가정한 보편적인 값이며, 필요에 따라 조정 가능하다.
"""

from __future__ import annotations

from ..models import Signal
from .metrics import FundamentalMetrics


def pe_signal(pe: float | None) -> Signal | None:
    """PER: 낮으면 저평가(매수), 높으면 고평가(매도). 음수는 적자 → 감점."""
    if pe is None:
        return None
    if pe <= 0:
        return Signal("PER", -0.5, f"PER {pe:.1f} → 적자(주의)")
    if pe < 15:
        return Signal("PER", 0.6, f"PER {pe:.1f} → 저평가(매수 우호)")
    if pe < 25:
        return Signal("PER", 0.2, f"PER {pe:.1f} → 적정 수준")
    if pe < 40:
        return Signal("PER", -0.3, f"PER {pe:.1f} → 다소 고평가")
    return Signal("PER", -0.6, f"PER {pe:.1f} → 고평가(매도 우호)")


def pb_signal(pb: float | None) -> Signal | None:
    """PBR: 1 미만이면 순자산 대비 저평가."""
    if pb is None:
        return None
    if pb < 1:
        return Signal("PBR", 0.5, f"PBR {pb:.2f} → 순자산 대비 저평가")
    if pb < 3:
        return Signal("PBR", 0.1, f"PBR {pb:.2f} → 적정 수준")
    return Signal("PBR", -0.4, f"PBR {pb:.2f} → 고평가")


def roe_signal(roe: float | None) -> Signal | None:
    """ROE: 자기자본이익률이 높을수록 수익성 우수. (비율, 예: 0.15 = 15%)"""
    if roe is None:
        return None
    if roe >= 0.20:
        return Signal("ROE", 0.6, f"ROE {roe:.1%} → 수익성 매우 우수")
    if roe >= 0.10:
        return Signal("ROE", 0.3, f"ROE {roe:.1%} → 양호한 수익성")
    if roe >= 0:
        return Signal("ROE", -0.1, f"ROE {roe:.1%} → 낮은 수익성")
    return Signal("ROE", -0.5, f"ROE {roe:.1%} → 적자")


def debt_signal(debt_to_equity: float | None) -> Signal | None:
    """부채비율: 낮을수록 재무 안정성 우수. (yfinance debtToEquity는 % 단위)"""
    if debt_to_equity is None:
        return None
    if debt_to_equity < 50:
        return Signal("DEBT", 0.4, f"부채비율 {debt_to_equity:.0f}% → 재무 안정적")
    if debt_to_equity < 150:
        return Signal("DEBT", 0.0, f"부채비율 {debt_to_equity:.0f}% → 보통")
    return Signal("DEBT", -0.5, f"부채비율 {debt_to_equity:.0f}% → 재무 부담")


def margin_signal(margin: float | None) -> Signal | None:
    """순이익률: 높을수록 우량. (비율, 예: 0.2 = 20%)"""
    if margin is None:
        return None
    if margin >= 0.20:
        return Signal("MARGIN", 0.4, f"순이익률 {margin:.1%} → 매우 우수")
    if margin >= 0.05:
        return Signal("MARGIN", 0.2, f"순이익률 {margin:.1%} → 양호")
    if margin >= 0:
        return Signal("MARGIN", -0.1, f"순이익률 {margin:.1%} → 낮음")
    return Signal("MARGIN", -0.5, f"순이익률 {margin:.1%} → 적자")


def fundamental_signals(metrics: FundamentalMetrics) -> list[Signal]:
    """사용 가능한 모든 재무 지표에서 신호 목록을 생성한다.

    데이터가 없는(None) 지표는 건너뛴다.
    """
    candidates = [
        pe_signal(metrics.pe_ratio),
        pb_signal(metrics.pb_ratio),
        roe_signal(metrics.roe),
        debt_signal(metrics.debt_to_equity),
        margin_signal(metrics.profit_margin),
    ]
    return [signal for signal in candidates if signal is not None]
