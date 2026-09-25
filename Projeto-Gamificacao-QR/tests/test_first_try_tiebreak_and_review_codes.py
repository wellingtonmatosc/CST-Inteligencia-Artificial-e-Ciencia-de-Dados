from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ranking_orders_by_points_stations_then_first_try():
    sql = read("supabase/migrations/20260925145000_first_try_tiebreak_and_test_question_codes.sql")
    compact = "".join(sql.split())
    assert "s.pointsdesc,s.stations_validateddesc,s.first_try_correctdesc" in compact
    assert "s.points,s.stations_validated,s.first_try_correct" in compact


def test_public_ranking_copy_matches_final_tiebreak_order():
    html = read("app/static/pages/ranking.html")
    js = read("app/static/js/ranking.js")
    assert "estações realizadas" in html
    assert "acertos na 1ª tentativa" in html
    assert "trilhas concluídas" not in js
    assert "first_try_correct" in js


def test_review_code_is_exposed_only_in_testing_state():
    sql = read("supabase/migrations/20260925145000_first_try_tiebreak_and_test_question_codes.sql")
    scan = read("app/static/js/scan.js")
    assert "is_testing" in sql
    assert "row_number() over (order by id)" in sql
    assert "'Q' || lpad" in sql
    assert "review_code" in sql
    assert "q.review_code" in scan
    assert "Desafio${reviewCode}" in scan
