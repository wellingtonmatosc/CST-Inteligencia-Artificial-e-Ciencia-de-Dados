from app.services.gamification_optimized import OptimizedGamificationService


class FakeRepo:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def rpc(self, name, payload=None):
        self.calls.append((name, payload or {}))
        return self.responses[name]


def test_get_qr_uses_single_rpc_for_normal_activity():
    repo = FakeRepo({
        "game_get_normal_activity": {
            "ok": True,
            "mode": "normal",
            "qr": {"code": "TESTE", "name": "Teste"},
            "run_id": "run-1",
            "status": "in_progress",
            "attempts": 0,
            "points_awarded": 0,
            "question": {"id": "q1", "kind": "true_false", "prompt": "Teste", "options": []},
        }
    })
    service = OptimizedGamificationService(repo, "America/Cuiaba")
    result = service.get_qr("participant-1", "TESTE")
    assert result["run_id"] == "run-1"
    assert [call[0] for call in repo.calls] == ["game_get_normal_activity"]


def test_answer_normal_uses_single_rpc():
    repo = FakeRepo({
        "game_answer_normal": {
            "ok": True,
            "correct": True,
            "completed": True,
            "points": 10,
            "milestones": [],
        }
    })
    service = OptimizedGamificationService(repo, "America/Cuiaba")
    result = service.answer_normal("participant-1", "run-1", "A")
    assert result == {"correct": True, "completed": True, "points": 10, "milestones": []}
    assert [call[0] for call in repo.calls] == ["game_answer_normal"]


def test_ranking_uses_single_rpc():
    ranking = [{"position": 1, "nick": "Teste", "points": 35}]
    repo = FakeRepo({"game_ranking": ranking})
    service = OptimizedGamificationService(repo, "America/Cuiaba")
    assert service.ranking() == ranking
    assert [call[0] for call in repo.calls] == ["game_ranking"]
