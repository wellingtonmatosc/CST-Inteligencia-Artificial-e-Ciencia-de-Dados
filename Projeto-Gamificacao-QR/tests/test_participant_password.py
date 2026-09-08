from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.core.security import hash_password, sha256_hex, verify_password
from app.services.moderation import NickModerationService
from app.services.participants import ParticipantService


class FakeQuery:
    def __init__(self, repo):
        self.repo = repo

    def select(self, *_args, **_kwargs):
        return self

    def ilike(self, _field, value):
        self.repo.nick_filter = value
        return self

    def eq(self, _field, _value):
        return self

    def limit(self, _value):
        return self

    def execute(self):
        participant = self.repo.participant
        if participant and participant["nick"].lower() == (self.repo.nick_filter or "").lower():
            return SimpleNamespace(data=[participant])
        return SimpleNamespace(data=[])


class FakeRepo:
    def __init__(self, participant):
        self.participant = participant
        self.nick_filter = None
        self.inserted_sessions = []

    def raw_table(self, table):
        assert table == "participants"
        return FakeQuery(self)

    def select(self, table, **filters):
        if table == "participants":
            if filters.get("access_code_hash") == self.participant.get("access_code_hash"):
                return [self.participant]
            return []
        if table == "blocked_terms":
            return []
        return []

    def insert(self, table, payload):
        if table == "participant_sessions":
            self.inserted_sessions.append(payload)
            return payload
        raise AssertionError(table)

    def update(self, table, payload, **filters):
        if table == "participants" and filters.get("id") == self.participant["id"]:
            self.participant.update(payload)
            return self.participant
        raise AssertionError((table, filters))


def make_service(pin="1234"):
    participant = {
        "id": "p1",
        "nick": "Wellington",
        "full_name": "Wellington Teste",
        "active": True,
        "password_hash": hash_password(pin),
        "access_code_hash": sha256_hex("ABCDEFGH"),
    }
    repo = FakeRepo(participant)
    service = ParticipantService(repo, NickModerationService(), session_days=30)
    return service, repo


def test_participant_login_with_nick_and_pin_creates_session():
    service, repo = make_service()
    participant, token = service.login("wellington", "1234")
    assert participant["id"] == "p1"
    assert token
    assert len(repo.inserted_sessions) == 1


def test_participant_login_rejects_wrong_pin():
    service, _ = make_service()
    with pytest.raises(AppError):
        service.login("Wellington", "9999")


def test_authenticated_participant_can_define_new_pin():
    service, repo = make_service()
    service.set_pin("p1", "5678")
    assert verify_password(repo.participant["password_hash"], "5678")


def test_recovery_rotates_code_and_sets_new_pin():
    service, repo = make_service()
    _, token, new_code = service.recover("ABCDEFGH", "2468")
    assert token
    assert new_code != "ABCDEFGH"
    assert verify_password(repo.participant["password_hash"], "2468")
    assert repo.participant["access_code_hash"] == sha256_hex(new_code)
