from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ranking_migration_tracks_transparent_merit_metrics():
    text = read("supabase/migrations/20260922164000_ranking_merits_final_tiebreak.sql").lower()
    assert "final_tiebreak_results" in text
    assert "correct_answers" in text
    assert "first_try_correct" in text
    assert "distinct_qrs" in text
    assert "active_days" in text
    assert "best_correct_streak" in text
    assert "final_tiebreak_score" in text


def test_ranking_order_does_not_use_speed_or_timestamp_as_tiebreak():
    text = read("supabase/migrations/20260922164000_ranking_merits_final_tiebreak.sql").lower()
    ranking_order = "s.points desc,\n        s.correct_answers desc,\n        s.first_try_correct desc,\n        s.distinct_qrs desc,\n        s.active_days desc,\n        s.final_tiebreak_score desc"
    assert ranking_order in text


def test_public_ranking_explains_final_rules():
    html = read("app/static/pages/ranking.html")
    js = read("app/static/js/ranking.js")
    assert "acertos na primeira tentativa" in html
    assert "Tempo e velocidade não são usados" in html
    assert "desempate supervisionado do Dia 7" in js


def test_admin_has_explicit_final_tiebreak_controls():
    common = read("app/static/js/common.js")
    admin = read("app/static/js/admin-ranking-rules.js")
    assert "/static/js/admin-ranking-rules.js" in common
    assert "/api/admin/final-tiebreak/" in admin
    assert "A nota não soma pontos" in admin
    assert "Dia 7 ainda sem data definida" in admin


def test_profile_exposes_merit_progress_without_extra_points():
    text = read("app/static/js/index.js")
    assert "Constância:" in text
    assert "Explorador:" in text
    assert "Sequência:" in text
    assert "Empate técnico" in text
