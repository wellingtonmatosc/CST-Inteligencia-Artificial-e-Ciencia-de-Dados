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


def test_latest_ranking_waits_for_whole_tiebreak_group():
    text = read("supabase/migrations/20260922165000_final_tiebreak_group_logic.sql").lower()
    assert "pre_final_tie_count" in text
    assert "final_scores_recorded_count" in text
    assert "effective_final_tiebreak_score" in text
    assert "final_scores_recorded_count = p.pre_final_tie_count" in text
    assert "unresolved_tie" in text
    assert "final_tiebreak_resolved" in text


def test_ranking_order_does_not_use_speed_as_tiebreak():
    text = read("supabase/migrations/20260922165000_final_tiebreak_group_logic.sql").lower()
    markers = [
        "p.points desc",
        "p.correct_answers desc",
        "p.first_try_correct desc",
        "p.distinct_qrs desc",
        "p.active_days desc",
        "p.effective_final_tiebreak_score desc",
    ]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "speed" not in text


def test_public_ranking_explains_final_rules():
    html = read("app/static/pages/ranking.html")
    js = read("app/static/js/ranking.js")
    assert "acertos na primeira tentativa" in html
    assert "Tempo e velocidade não são usados" in html
    assert "desempate supervisionado do Dia 7" in js
    assert "unresolved_tie" in js


def test_admin_has_explicit_final_tiebreak_controls():
    common = read("app/static/js/common.js")
    admin = read("app/static/js/admin-ranking-rules.js")
    assert "/static/js/admin-ranking-rules.js" in common
    assert "/api/admin/final-tiebreak/" in admin
    assert "A nota não soma pontos" in admin
    assert "grupo inteiro estiver preenchido" in admin
    assert "Dia 7 ainda sem data definida" in admin


def test_profile_exposes_merit_progress_without_extra_points():
    text = read("app/static/js/index.js")
    assert "Constância:" in text
    assert "Explorador:" in text
    assert "Sequência:" in text
    assert "unresolved_tie" in text
