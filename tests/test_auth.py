from app.auth import hash_password, read_session, sign_session, verify_password


def test_password_hash_roundtrip():
    stored = hash_password("correct horse")
    assert stored.startswith("pbkdf2_sha256$")
    assert "correct horse" not in stored
    assert verify_password("correct horse", stored)
    assert not verify_password("wrong horse", stored)


def test_session_cookie_roundtrip(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret-value-0123456789")
    token = sign_session(7)
    assert read_session(token) == 7
    assert read_session(token + "x") is None
    assert read_session(None) is None
