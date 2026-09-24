from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260924114944_manual_event_lifecycle_and_test_mode.sql"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_event_can_run_from_one_to_seven_days_and_has_test_mode():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "duration_days between 1 and 7" in sql
    assert "status in ('draft','testing','running','ended')" in sql
    assert "trilhas_admin_set_test_mode" in sql
    assert "america/cuiaba" in sql


def test_official_start_resets_competition_but_not_participants():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "delete from public.station_attempts" in sql
    assert "delete from public.station_visits" in sql
    assert "delete from public.point_ledger" in sql
    assert "delete from public.participants" not in sql
    assert "event_not_ready" in sql


def test_balanced_pool_targets_300_questions_and_15_qrs():
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "v_questions <> 300" in sql
    assert "v_qrs <> 15" in sql
    assert "% 15" in sql
    assert "questions_per_qr',20" in sql


def test_admin_uses_new_event_control_and_hides_legacy_workflows():
    common = read("app/static/js/common.js")
    event_ui = read("app/static/js/admin-event-control.js")
    assert "/static/js/admin-event-control.js" in common
    assert "/static/js/admin-question-pool.js" not in common
    assert "hideTab('pointsPanel')" in event_ui
    assert "hideTab('settingsPanel')" in event_ui
    assert "contentForm" in event_ui
    assert "questionForm" in event_ui
    assert "Iniciar evento oficial" in event_ui
