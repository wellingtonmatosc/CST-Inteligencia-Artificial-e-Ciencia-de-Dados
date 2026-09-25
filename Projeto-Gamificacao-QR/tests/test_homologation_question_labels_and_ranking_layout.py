from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mobile_ranking_resets_legacy_grid_areas_and_allows_nick_wrap():
    css = read("app/static/css/ranking-homologation-fixes.css").replace(" ", "")
    assert "grid-area:auto!important" in css
    assert "grid-column:auto!important" in css
    assert "grid-row:auto!important" in css
    assert "white-space:normal!important" in css
    assert "text-overflow:clip!important" in css
    assert "grid-template-columns:38px40pxminmax(0,1fr)56px!important" in css


def test_question_reference_migration_preserves_roman_questions_and_normalizes_letters():
    sql = read("supabase/migrations/20260925142000_normalize_question_reference_labels.sql")
    compact = sql.replace(" ", "").replace("\n", "")
    assert "chr(10)||'a)'" in compact
    assert "chr(10)||'A)'" in compact
    assert "\\ma\\M" in sql
    assert "\\md\\M" in sql
    assert "algarismos romanos" in sql
    assert "correct_answer" in sql.lower()
    assert "set options" in sql.lower()
