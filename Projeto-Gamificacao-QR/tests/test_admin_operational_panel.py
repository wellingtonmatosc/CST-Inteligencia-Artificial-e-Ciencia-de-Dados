from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_admin_navigation_matches_current_event_scope():
    html = read("app/static/pages/admin.html")
    for label in ("Visão geral", "Participantes", "QRs", "Questões", "Análises", "Ranking", "Auditoria"):
        assert label in html
    assert 'data-admin-tab="trailsPanel"' not in html
    assert 'data-admin-tab="pointsPanel"' not in html
    assert "Criar questão" not in html
    assert "Conteúdo cultural da estação" not in html


def test_admin_loads_only_current_operational_modules():
    html = read("app/static/pages/admin.html")
    assert '/static/js/admin.js' in html
    assert '/static/js/admin-analytics.js' in html
    assert '/static/js/admin-question-pool.js' not in html
    assert '/static/js/admin-monitoring.js' not in html
    assert '/static/js/admin-ranking-rules.js' not in html
    assert '/static/js/admin-event-control.js' not in html


def test_admin_question_review_codes_are_searchable_and_editable():
    html = read("app/static/pages/admin.html")
    js = read("app/static/js/admin.js")
    assert "Buscar Q137" in html
    assert "review_code" in js
    assert "method:'PUT'" in js
    assert "Salvar correção" in html


def test_admin_ranking_uses_current_three_level_rule():
    html = read("app/static/pages/admin.html").lower()
    dashboard = read("app/api/admin_dashboard.py")
    assert "pontos → estações realizadas → acertos na 1ª tentativa" in html
    assert '["points", "stations_validated", "first_try_correct"]' in dashboard


def test_admin_qr_editor_does_not_offer_legacy_station_types_or_creation():
    html = read("app/static/pages/admin.html")
    js = read("app/static/js/admin.js")
    assert "Criar estação" not in html
    assert "temporary" not in html
    assert "special" not in html
    assert "station_type:'permanent'" in js
    assert "base_points:10" in js


def test_admin_analytics_cover_requested_views_and_extra_quality_checks():
    html = read("app/static/pages/admin.html")
    js = read("app/static/js/admin-analytics.js")
    migration = read("supabase/migrations/20260925154500_admin_analytics.sql")
    for item in ("QRs utilizados por dia", "Uso por QR", "Ranking geral", "Ranking por dia", "Ranking por questões", "Ranking por QRs", "1ª x 2ª tentativa", "Questões com mais dificuldade", "Taxa de acerto por QR"):
        assert item in html
    assert "question_performance" in js
    assert "trilhas_admin_analytics" in migration
    assert "first_try_correct" in migration


def test_manual_points_are_presented_only_as_exceptional_correction():
    html = read("app/static/pages/admin.html")
    js = read("app/static/js/admin.js")
    assert "Correção administrativa de pontuação" in html
    assert "Digite CORRIGIR" in html
    assert "action_type:'other'" in js
    assert "Declamação" not in html
    assert "Postagem válida" not in html
