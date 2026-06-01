"""CLI 검증 (--demo 모드, 네트워크 불필요)."""

from __future__ import annotations

import json

import pytest

from stock_analyzer.cli import main


def test_analyze_demo(capsys):
    rc = main(["analyze", "AAPL", "--demo"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "[AAPL]" in out
    assert "추천:" in out


def test_analyze_with_news_demo(capsys):
    rc = main(["analyze", "NVDA", "--demo", "--news"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "뉴스 점수" in out
    assert "뉴스" in out and "평균 감성" in out


def test_analyze_json_demo(capsys):
    rc = main(["analyze", "MSFT", "--demo", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["ticker"] == "MSFT"
    assert "recommendation" in data
    assert "composite_score" in data


def test_news_demo(capsys):
    rc = main(["news", "AI", "--demo", "--limit", "5"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "다이제스트" in out
    assert "시장 영향" in out


def test_chart_demo(tmp_path, capsys):
    out_path = tmp_path / "chart.png"
    rc = main(["chart", "TSLA", "--demo", "--out", str(out_path)])
    assert rc == 0
    assert out_path.exists() and out_path.stat().st_size > 0


def test_deterministic_demo(capsys):
    """같은 티커는 항상 같은 결과를 내야 한다."""
    main(["analyze", "AAPL", "--demo", "--json"])
    first = capsys.readouterr().out
    main(["analyze", "AAPL", "--demo", "--json"])
    second = capsys.readouterr().out
    assert first == second


def test_unknown_command_errors():
    with pytest.raises(SystemExit):
        main(["bogus"])
