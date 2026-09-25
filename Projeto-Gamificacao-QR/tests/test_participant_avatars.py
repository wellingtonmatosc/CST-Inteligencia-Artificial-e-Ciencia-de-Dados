from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.api.deps import current_participant
from app.api.participants import AvatarPayload, RegisterPayload, update_avatar
from app.core.avatars import AVATAR_KEYS, DEFAULT_AVATAR_KEY, validate_avatar_key
from app.core.errors import AppError
from app.services.trilhas import TrilhasService

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def base_register(**overrides):
    payload = {
        "full_name": "Participante Teste",
        "nick": "AvatarTeste",
        "pin": "1234",
        "participant_type": "external",
    }
    payload.update(overrides)
    return payload


def test_catalog_has_twenty_internal_avatar_keys_and_default():
    assert len(AVATAR_KEYS) == 20
    assert AVATAR_KEYS[0] == DEFAULT_AVATAR_KEY == "avatar-01"
    assert AVATAR_KEYS[-1] == "avatar-20"
    assert validate_avatar_key(None) == DEFAULT_AVATAR_KEY


def test_registration_accepts_valid_avatar_and_defaults_when_omitted():
    chosen = RegisterPayload(**base_register(avatar_key="avatar-20"))
    defaulted = RegisterPayload(**base_register())
    assert chosen.avatar_key == "avatar-20"
    assert defaulted.avatar_key == DEFAULT_AVATAR_KEY


@pytest.mark.parametrize("value", ["../../arquivo", "https://site.com/imagem.png", "avatar-21", "avatar-00", "foto.png"])
def test_registration_rejects_arbitrary_or_external_avatar_values(value):
    with pytest.raises(ValidationError):
        RegisterPayload(**base_register(avatar_key=value))
    with pytest.raises(ValueError):
        validate_avatar_key(value)


def test_avatar_payload_accepts_only_catalog_key():
    assert AvatarPayload(avatar_key="avatar-20").avatar_key == "avatar-20"
    with pytest.raises(ValidationError):
        AvatarPayload(avatar_key="avatar-x")


def test_authenticated_avatar_route_updates_only_current_participant():
    class Service:
        def __init__(self):
            self.called = None
        def update_avatar(self, participant_id, avatar_key):
            self.called = (participant_id, avatar_key)
            return avatar_key

    service = Service()
    result = update_avatar(AvatarPayload(avatar_key="avatar-16"), participant={"id": "participant-current"}, service=service)
    assert service.called == ("participant-current", "avatar-16")
    assert result == {"ok": True, "avatar_key": "avatar-16"}


def test_unauthenticated_participant_dependency_rejects_avatar_change_context():
    request = Request({"type": "http", "method": "PATCH", "path": "/api/participants/avatar", "headers": []})
    settings = SimpleNamespace(participant_cookie_name="participant_session")
    with pytest.raises(AppError) as exc:
        current_participant(request, service=object(), settings=settings)
    assert exc.value.status_code == 401


def test_me_and_frontend_expose_avatar_key_and_change_action():
    api_text = read("app/api/participants.py")
    index_html = read("app/static/pages/index.html")
    index_js = read("app/static/js/index.js")
    assert '"avatar_key": participant.get("avatar_key")' in api_text
    assert 'id="registerAvatarPicker"' in index_html
    assert "/static/js/avatars.js" in index_html
    assert "/api/participants/avatar" in index_js
    assert "Trocar avatar" in index_js


def test_migrations_keep_default_avatar_and_expand_catalog_to_twenty():
    initial = read("supabase/migrations/20260922190000_participant_avatars.sql")
    expanded = read("supabase/migrations/20260923135000_expand_participant_avatar_catalog.sql")
    assert "add column if not exists avatar_key text not null default 'avatar-01'" in initial
    assert "participants_avatar_key_check" in initial
    assert "participants_avatar_key_check" in expanded
    assert "avatar-(0[1-9]|1[0-9]|20)" in expanded
    assert "'avatar_key',v_p.avatar_key" in initial.replace(" ", "")


def test_public_ranking_keeps_avatar_but_removes_private_id():
    class Repo:
        def rpc(self, name, _payload):
            assert name == "trilhas_individual_ranking"
            return [{"id": "private-id", "nick": "Pessoa", "avatar_key": "avatar-13", "points": 20}]

    rows = TrilhasService(Repo()).ranking()
    assert rows == [{"nick": "Pessoa", "avatar_key": "avatar-13", "points": 20}]


def test_avatar_migration_does_not_change_ranking_order_or_speed_rules():
    text = read("supabase/migrations/20260922190000_participant_avatars.sql").lower()
    markers = [
        "p.points desc",
        "p.correct_answers desc",
        "p.first_try_correct desc",
        "p.distinct_qrs desc",
        "p.active_days desc",
        "p.effective_final_tiebreak_score desc",
    ]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "speed" not in text
    assert "avatar_key desc" not in text
    assert "avatar_key asc" not in text


def test_avatar_visuals_are_local_webp_without_external_image_urls():
    text = read("app/static/js/avatars.js")
    avatar_dir = ROOT / "app/static/assets/avatars"
    files = sorted(avatar_dir.glob("*.webp"))
    assert len(files) == 20
    assert "<img" in text
    assert "/static/assets/avatars" in text
    assert ".webp" in text
    assert "https://" not in text
    assert "http://" not in text
    assert "upload" not in text.lower()
