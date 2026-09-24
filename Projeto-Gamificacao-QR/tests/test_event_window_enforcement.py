from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260924105817_enforce_event_day_window.sql"
SERVICE = ROOT / "app" / "services" / "trilhas.py"


def test_event_requires_all_seven_dates_before_competition_is_open():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "v_active_days <> 7 or v_configured_days <> 7" in sql
    assert "event_not_configured" in sql
    assert "america/cuiaba" in sql


def test_event_gate_distinguishes_before_after_and_inactive_day():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "event_not_started" in sql
    assert "event_ended" in sql
    assert "event_not_active_today" in sql


def test_station_validation_is_blocked_without_current_event_day():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    marker = "v_event_state := public.trilhas_event_state();"
    assert sql.count(marker) >= 3
    assert "v_event_day := (v_event_state->>'day_number')::smallint" in sql


def test_answer_only_uses_visit_from_current_local_event_day():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "and activity_date = v_today" in sql
    assert "and assigned_event_day = v_event_day" in sql
    assert "order by case when activity_date=v_today" not in sql


def test_event_state_rpc_is_not_executable_by_browser_roles():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "revoke execute on function public.trilhas_event_state() from public, anon, authenticated" in sql
    assert "grant execute on function public.trilhas_event_state() to service_role" in sql


def test_service_has_clear_messages_for_event_window_errors():
    text = SERVICE.read_text(encoding="utf-8")
    assert "event_not_configured" in text
    assert "event_not_started" in text
    assert "event_not_active_today" in text
    assert "event_ended" in text
    assert "Valide esta estação hoje" in text
