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


def _multiple_choice_station(_payload):
    return {
        "ok": True,
        "qr": {"station_type": "permanent", "name": "Teste"},
        "question": {
            "id": "question-1",
            "kind": "multiple_choice",
            "prompt": "Escolha uma alternativa",
            "options": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
                {"label": "C", "value": "c"},
                {"label": "D", "value": "d"},
            ],
        },
    }


def test_multiple_choice_order_is_stable_for_same_participant_and_question():
    repo = FakeRepo({"trilhas_get_station": _multiple_choice_station})
    service = TrilhasService(repo)

    first = service.get_station("participant-1", "QR1")["question"]["options"]
    second = service.get_station("participant-1", "QR1")["question"]["options"]

    assert first == second
    assert {item["value"] for item in first} == {"a", "b", "c", "d"}


def test_multiple_choice_order_varies_between_participants():
    repo = FakeRepo({"trilhas_get_station": _multiple_choice_station})
    service = TrilhasService(repo)

    orders = {
        tuple(item["value"] for item in service.get_station(f"participant-{n}", "QR1")["question"]["options"])
        for n in range(1, 21)
    }

    assert len(orders) > 1


def test_true_false_keeps_original_order():
    def station(_payload):
        return {
            "ok": True,
            "qr": {"station_type": "permanent", "name": "Teste"},
            "question": {
                "id": "question-vf",
                "kind": "true_false",
                "prompt": "Verdadeiro ou falso?",
                "options": [
                    {"label": "Verdadeiro", "value": "true"},
                    {"label": "Falso", "value": "false"},
                ],
            },
        }

    repo = FakeRepo({"trilhas_get_station": station})
    options = TrilhasService(repo).get_station("participant-1", "QR1")["question"]["options"]

    assert [item["value"] for item in options] == ["true", "false"]


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
