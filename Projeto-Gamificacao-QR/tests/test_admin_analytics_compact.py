from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_analytics_uses_single_filtered_workspace():
    text = read("app/static/js/admin-analytics.js")
    assert "analysisGroupSelect" in text
    assert "analysisType" in text
    assert "analysisDay" in text
    assert "analysisLimit" in text
    assert "analytics-workspace" in text
    assert "Ranking geral" in text
    assert "Ranking por acertos na 1ª tentativa" in text
    assert "Questões com mais dificuldade" in text


def test_analysis_groups_are_separate_native_filters():
    text = read("app/static/js/admin-analytics.js")
    assert "const GROUPS=['Competição','Uso dos QRs','Qualidade das questões']" in text
    assert "syncAnalysisOptions" in text
    assert "analysisOptions(group" in text


def test_rank_layout_matches_current_three_outer_blocks():
    css = read("app/static/css/admin-ops.css")
    assert "grid-template-columns:44px minmax(0,1fr) auto!important" in css
    assert "grid-template-areas:\"avatar name\" \"avatar meta\"!important" in css
    assert "#adminRankingList .admin-rank" in css
    assert "#rankingPreview .admin-rank" in css


def test_qr_usage_and_daily_usage_are_horizontal_and_descending():
    js = read("app/static/js/admin-analytics.js")
    assert "function renderQrUsage" in js
    assert "Number(b.validations||0)-Number(a.validations||0)" in js
    assert "function renderDailyUsage" in js
    assert "horizontalBars(el,rows" in js


def test_question_difficulty_has_line_break_between_count_and_prompt():
    js = read("app/static/js/admin-analytics.js")
    css = read("app/static/css/admin-ops.css")
    assert "resposta(s)\\n" in js
    assert "white-space:pre-line" in css


def test_qr_accuracy_uses_grouped_vertical_columns():
    js = read("app/static/js/admin-analytics.js")
    css = read("app/static/css/admin-ops.css")
    assert "groupedAccuracyColumns" in js
    assert "first_rate" in js
    assert "second_rate" in js
    assert "total_rate" in js
    assert ".grouped-column-chart" in css
    assert ".grouped-first" in css
    assert ".grouped-second" in css
    assert ".grouped-total" in css
    assert "height:254px" in css
