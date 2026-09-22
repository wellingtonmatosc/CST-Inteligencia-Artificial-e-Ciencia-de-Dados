from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_legacy_schema_copy_was_removed():
    assert not (ROOT / "supabase" / "schema.sql").exists()


def test_seed_contains_only_base_catalog_not_event_data():
    seed = read("supabase/seed.sql").lower()
    assert "insert into public.categories" in seed
    assert "insert into public.zones" in seed
    for table in ("questions", "participants", "qr_points", "station_visits", "point_ledger"):
        assert f"insert into public.{table}" not in seed


def test_station_ui_is_multiple_choice_only_and_supports_optional_physical_code():
    scan = read("app/static/js/scan.js")
    assert "true_false" not in scan
    assert "short_text" not in scan
    assert "state.requires_physical_code" in scan
    assert "physicalCode=physicalField?" in scan


def test_admin_final_ui_has_no_old_question_types_or_variable_station_scoring():
    html = read("app/static/pages/admin.html")
    js = read("app/static/js/admin.js")
    assert "Verdadeiro/Falso" not in html
    assert "Resposta curta" not in html
    assert "Sequencial — 15" not in html
    assert "Temporária — 30" not in html
    assert "Especial — 40" not in html
    assert "base_points:10" in js
    assert "kind:'multiple_choice'" in js


def test_accessibility_control_is_not_created_as_floating_overlay():
    common = read("app/static/js/common.js")
    assert "createInlineA11yToggle" in common
    assert "document.body.append(toggle,panel)" not in common
