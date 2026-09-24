from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_main_registers_question_pool_router():
    text = read("app/main.py")
    assert "question_pool" in text
    assert "app.include_router(question_pool.router)" in text


def test_admin_loads_manual_event_control_instead_of_legacy_pool_ui():
    text = read("app/static/js/common.js")
    assert "location.pathname==='/admin'" in text
    assert "/static/js/admin-event-control.js" in text
    assert "/static/js/admin-question-pool.js" not in text


def test_manual_event_control_supports_one_to_seven_days_and_test_mode():
    text = read("app/static/js/admin-event-control.js")
    assert "competição individual de 1 a 7 dias" in text
    assert "/api/admin/event-control/testing" in text
    assert "Iniciar evento oficial" in text
    assert "Dia simulado no teste" in text


def test_migration_preserves_legacy_fallback_and_assigns_question_to_visit():
    text = read("supabase/migrations/20260918153000_question_pool_event_days.sql")
    assert "create table if not exists public.station_question_pool" in text.lower()
    assert "create table if not exists public.event_days" in text.lower()
    assert "between 1 and 7" in text.lower()
    assert "sc.challenge_question_id" in text
    assert "v_question_id := public.trilhas_select_station_question" in text
    assert "v_visit.question_id" in text
    assert "assigned_event_day" in text


def test_pool_does_not_expose_correct_answer_in_legacy_admin_listing_script():
    text = read("app/static/js/admin-question-pool.js")
    assert "correct_answer" not in text
