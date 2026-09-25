from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ranking_uses_current_avatar_and_no_visible_medal_words():
    js = read("app/static/js/ranking.js")
    assert "r.avatar_key" in js
    assert "Ouro" not in js
    assert "Prata" not in js
    assert "Bronze" not in js


def test_ranking_mobile_fix_neutralizes_legacy_grid():
    html = read("app/static/pages/ranking.html")
    css = read("app/static/css/ranking-homologation-fixes.css")
    assert "/static/css/ranking-homologation-fixes.css" in html
    assert "display:block!important" in css.replace(" ", "")
    assert "grid-template-columns:repeat(2,minmax(0,1fr))!important" in css.replace(" ", "")


def test_migration_exposes_avatar_and_normalizes_literal_newlines():
    sql = read("supabase/migrations/20260925133500_fix_ranking_avatar_and_question_newlines.sql")
    compact = sql.replace(" ", "").replace("\n", "")
    assert "p.avatar_key" in sql
    assert "'avatar_key',avatar_key" in compact
    assert "replace(prompt,chr(92)||'n',chr(10))" in compact
