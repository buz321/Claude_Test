"""차트 시각화 검증.

GUI 없이 PNG 파일이 정상적으로 생성되는지만 확인한다.
matplotlib가 없으면 테스트를 건너뛴다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("matplotlib")

from stock_analyzer import StockAnalyzer  # noqa: E402
from stock_analyzer.viz import plot_analysis  # noqa: E402


@pytest.fixture
def sample_close() -> pd.Series:
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    rng = np.random.default_rng(0)
    values = np.linspace(100, 180, 250) + rng.normal(0, 2, 250)
    return pd.Series(values, index=dates, name="Close")


def test_plot_analysis_saves_png(sample_close, tmp_path):
    out = tmp_path / "chart.png"
    fig, axes = plot_analysis(sample_close, save_path=str(out))
    assert out.exists()
    assert out.stat().st_size > 0
    assert len(axes) == 3  # price, RSI, MACD


def test_analyzer_plot_method(sample_close, tmp_path, mock_provider_factory):
    provider = mock_provider_factory(
        sample_close, {"trailingPE": 18.0, "returnOnEquity": 0.2}
    )
    out = tmp_path / "analysis.png"
    result, fig = StockAnalyzer("TEST", provider=provider).plot(save_path=str(out))
    assert out.exists()
    assert result.ticker == "TEST"
