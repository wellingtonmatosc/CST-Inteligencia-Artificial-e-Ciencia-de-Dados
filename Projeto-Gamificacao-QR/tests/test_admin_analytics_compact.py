from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_analytics_uses_single_filtered_workspace():
    text = read("app/static/js/admin-analytics.js")
    assert "analysisType" in text
    assert "analysisDay" in text
    assert "analysisLimit" in text
    assert "analytics-workspace" in text
    assert "Ranking geral" in text
    assert "Ranking por acertos na 1ª tentativa" in text
    assert "Questões com mais dificuldade" in text


def test_rank_layout_matches_current_three_outer_blocks():
    css = read("app/static/css/admin-ops.css")
    assert "grid-template-columns:44px minmax(0,1fr) auto!important" in css
    assert "grid-template-areas:\"avatar name\" \"avatar meta\"!important" in css
    assert "#adminRankingList .admin-rank" in css
    assert "#rankingPreview .admin-rank" in css


def test_analytics_has_horizontal_and_vertical_visualizations():
    css = read("app/static/css/admin-ops.css")
    js = read("app/static/js/admin-analytics.js")
    assert ".horizontal-chart" in css or "horizontal-chart" in js
    assert ".vertical-chart" in css or "vertical-chart" in js
    assert "verticalColumns" in js
    assert "horizontalBars" in js
