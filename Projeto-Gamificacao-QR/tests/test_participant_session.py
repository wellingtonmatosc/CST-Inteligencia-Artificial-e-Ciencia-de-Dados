from datetime import datetime

from app.core.security import sha256_hex
from app.services.moderation import NickModerationService
from app.services.participants import ParticipantService


class FakeRepo:
    def __init__(self):
        self.updates = []

    def update(self, table, payload, **filters):
        self.updates.append((table, payload, filters))
        return []


def test_logout_revokes_current_session_by_token_hash():
    repo = FakeRepo()
    service = ParticipantService(repo, NickModerationService())

    service.logout("token-de-teste")

    assert len(repo.updates) == 1
    table, payload, filters = repo.updates[0]
    assert table == "participant_sessions"
    assert filters == {"token_hash": sha256_hex("token-de-teste")}
    assert "revoked_at" in payload
    datetime.fromisoformat(payload["revoked_at"])


def test_logout_without_cookie_is_idempotent():
    repo = FakeRepo()
    service = ParticipantService(repo, NickModerationService())

    service.logout(None)

    assert repo.updates == []
