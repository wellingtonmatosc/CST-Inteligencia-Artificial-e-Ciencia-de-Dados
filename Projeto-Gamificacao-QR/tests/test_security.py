from app.core.security import hash_password, random_access_code, sign_admin_session, verify_admin_session, verify_password


def test_password_hash_roundtrip():
    hashed=hash_password("senha-de-teste-123")
    assert verify_password(hashed,"senha-de-teste-123") is True
    assert verify_password(hashed,"outra") is False


def test_admin_session_roundtrip():
    token=sign_admin_session("segredo-super-seguro")
    assert verify_admin_session("segredo-super-seguro",token,60) is True
    assert verify_admin_session("outro-segredo",token,60) is False


def test_access_code_has_expected_length():
    assert len(random_access_code())==8
