import pytest

from app.core.errors import AppError
from app.services.trilhas import TrilhasService


class FakeRepo:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def rpc(self, name, payload=None):
        self.calls.append((name, payload or {}))
        value = self.responses[name]
        return value(payload or {}) if callable(value) else value


def test_get_station_maps_station_type_label():
    repo = FakeRepo({"trilhas_get_station": {"ok": True, "qr": {"station_type": "temporary", "name": "Teste"}}})
    data = TrilhasService(repo).get_station("p1", "ABC")
    assert data["qr"]["station_type_label"] == "Temporário"
    assert repo.calls[0][0] == "trilhas_get_station"


def test_validate_station_reports_sequence_lock():
    repo = FakeRepo({"trilhas_validate_station": {"ok": False, "error": "sequence_locked"}})
    with pytest.raises(AppError) as exc:
        TrilhasService(repo).validate_station("p1", "QR2", "CODIGO")
    assert exc.value.status_code == 409
    assert "etapas anteriores" in exc.value.message


def test_answer_challenge_returns_success_payload():
    expected = {"ok": True, "correct": True, "points": 10, "completed": True}
    repo = FakeRepo({"trilhas_answer_challenge": expected})
    result = TrilhasService(repo).answer_challenge("p1", "QR1", "verso")
    assert result == expected


def test_ranking_returns_empty_list_for_invalid_backend_payload():
    repo = FakeRepo({"trilhas_team_ranking": {"unexpected": True}})
    assert TrilhasService(repo).ranking() == []


def test_ranking_keeps_team_rows():
    rows = [{"name": "Equipe Pagu", "position": None, "points": 0}]
    repo = FakeRepo({"trilhas_team_ranking": rows})
    assert TrilhasService(repo).ranking() == rows
