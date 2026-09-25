from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_MIGRATION = ROOT / "supabase" / "migrations" / "20260924105100_align_final_scoring_and_ranking.sql"
LATEST_RANKING_MIGRATION = ROOT / "supabase" / "migrations" / "20260925145000_first_try_tiebreak_and_test_question_codes.sql"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_latest_ranking_uses_official_three_level_order():
    text = LATEST_RANKING_MIGRATION.read_text(encoding="utf-8").lower()
    compact = "".join(text.split())
    assert "s.pointsdesc,s.stations_validateddesc,s.first_try_correctdesc" in compact
    assert "s.points,s.stations_validated,s.first_try_correct" in compact


def test_real_ties_share_position():
    text = LATEST_RANKING_MIGRATION.read_text(encoding="utf-8").lower()
    assert "rank() over" in text
    assert "'tie_count',tie_count" in text.replace(" ", "")
    assert "'is_tied',tie_count>1" in text.replace(" ", "")


def test_trail_completion_is_progress_only_and_does_not_award_points():
    text = BASE_MIGRATION.read_text(encoding="utf-8").lower()
    assert "points_awarded\n  ) values (\n    p_participant_id,\n    v_s.trail_id,\n    0" in text
    assert "nao cria entrada de pontuacao no point_ledger" in text
    assert "'trail_completion'" not in text


def test_official_points_exclude_historical_trail_bonus():
    text = BASE_MIGRATION.read_text(encoding="utf-8").lower()
    assert "'station_validation'" in text
    assert "'challenge'" in text
    assert "'manual_action'" in text
    assert "'manual_reversal'" in text
    assert "'trail_completion'" not in text


def test_public_ranking_explains_current_rules():
    html = read("app/static/pages/ranking.html").lower()
    js = read("app/static/js/ranking.js").lower()
    assert "estações realizadas" in html
    assert "acertos na 1ª tentativa" in html
    assert "compartilham a mesma posição" in html
    assert "trails_completed" not in js
    assert "stations_validated" in js
    assert "first_try_correct" in js
    assert "empate • mesma posição" in js


def test_admin_ranking_matches_current_rules_without_supervised_tiebreak():
    admin = read("app/static/js/admin-ranking-rules.js").lower()
    assert "pontos acumulados, estações realizadas e acertos na 1ª tentativa" in admin
    assert "estações realizadas •" in admin
    assert "first_try_correct" in admin
    assert "/api/admin/final-tiebreak/" not in admin
    assert "resultado supervisionado" not in admin
