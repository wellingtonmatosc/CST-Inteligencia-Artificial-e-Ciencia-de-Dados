from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260922161500_daily_event_competition_rules.sql"
INDEX_HTML = ROOT / "app" / "static" / "pages" / "index.html"
SCAN_JS = ROOT / "app" / "static" / "js" / "scan.js"
MONITOR_JS = ROOT / "app" / "static" / "js" / "admin-monitoring.js"


def test_qr_is_unique_per_participant_and_local_day():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "uq_station_visits_participant_qr_day" in sql
    assert "participant_id, qr_point_id, activity_date" in sql
    assert "America/Cuiaba" in sql


def test_question_selection_never_falls_back_to_seen_pool_question():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "not exists" in sql
    assert "previous_visit.question_id = sqp.question_id" in sql
    assert "Pool configurado e esgotado" in sql
    assert "return v_question_id" in sql


def test_scoring_is_10_first_attempt_and_6_second_attempt():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "when v_attempt = 1 then 10" in sql
    assert "else 6" in sql
    assert "v_points := 10" in sql


def test_second_attempt_keeps_previous_wrong_option_blocked():
    js = SCAN_JS.read_text(encoding="utf-8")
    assert "priorWrongAnswers" in js
    assert "tentativa já utilizada" in js
    assert "até +${nextPoints} pontos" in js


def test_registration_has_no_email_registration_class_or_semester_fields():
    html = INDEX_HTML.read_text(encoding="utf-8").lower()
    assert 'name="campus' not in html  # campus is resolved from predefined/custom controls in JS
    assert "campus_select" in html
    assert "course_select" in html
    assert "outro campus" in html
    assert "outro curso" in html
    assert 'name="email"' not in html
    assert 'name="registration"' not in html
    assert 'name="course_class"' not in html
    assert 'name="semester"' not in html


def test_access_monitoring_is_signal_only():
    js = MONITOR_JS.read_text(encoding="utf-8")
    assert "Horário incomum" in js
    assert "Apenas sinalizado" in js
    assert "bloqueios automáticos" in js
