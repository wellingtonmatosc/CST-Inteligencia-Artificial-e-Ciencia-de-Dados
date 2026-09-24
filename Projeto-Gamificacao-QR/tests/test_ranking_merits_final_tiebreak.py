from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260924105100_align_final_scoring_and_ranking.sql"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_latest_ranking_uses_official_three_level_order():
    text = MIGRATION.read_text(encoding="utf-8").lower()
    ranking_order = "s.points desc,\n        s.trails_completed desc,\n        s.stations_validated desc"
    assert ranking_order in text
    assert "partition by\n        s.points,\n        s.trails_completed,\n        s.stations_validated" in text


def test_real_ties_share_position():
    text = MIGRATION.read_text(encoding="utf-8").lower()
    assert "rank() over" in text
    assert "'tie_count', tie_count" in text
    assert "'is_tied', tie_count > 1" in text


def test_trail_completion_is_progress_only_and_does_not_award_points():
    text = MIGRATION.read_text(encoding="utf-8").lower()
    assert "points_awarded\n  ) values (\n    p_participant_id,\n    v_s.trail_id,\n    0" in text
    assert "nao cria entrada de pontuacao no point_ledger" in text
    assert "'trail_completion'" not in text


def test_official_points_exclude_historical_trail_bonus():
    text = MIGRATION.read_text(encoding="utf-8").lower()
    assert "'station_validation'" in text
    assert "'challenge'" in text
    assert "'manual_action'" in text
    assert "'manual_reversal'" in text
    assert "'trail_completion'" not in text


def test_public_ranking_explains_current_rules():
    html = read("app/static/pages/ranking.html").lower()
    js = read("app/static/js/ranking.js").lower()
    assert "trilhas concluídas" in html
    assert "estações realizadas" in html
    assert "compartilham a mesma posição" in html
    assert "trails_completed" in js
    assert "stations_validated" in js
    assert "empate • mesma posição" in js


def test_admin_ranking_no_longer_exposes_supervised_final_tiebreak():
    admin = read("app/static/js/admin-ranking-rules.js").lower()
    assert "pontos acumulados, trilhas concluídas e estações realizadas" in admin
    assert "trilhas não geram pontos extras" in admin
    assert "/api/admin/final-tiebreak/" not in admin
    assert "resultado supervisionado" not in admin
