from app.services.moderation import NickModerationService, normalize_for_moderation


def test_normalization_handles_basic_obfuscation():
    assert normalize_for_moderation("T3.s-t3") == "teste"


def test_configurable_blocked_term():
    service=NickModerationService("termoexemplo")
    ok,_=service.validate("t3rm0.exemplo")
    assert ok is False


def test_normal_nick_is_allowed_without_configured_terms():
    ok,reason=NickModerationService().validate("Wellington_IA")
    assert ok is True
    assert reason is None
