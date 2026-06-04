import pytest

from app.utils.security import hash_password, verify_password


def test_hash_and_verify():
    senha = "MinhaSenha123!"
    hashed = hash_password(senha)
    assert hashed != senha
    assert verify_password(senha, hashed)


def test_wrong_password_fails():
    hashed = hash_password("correta")
    assert not verify_password("errada", hashed)


def test_different_hashes_for_same_password():
    h1 = hash_password("senha")
    h2 = hash_password("senha")
    assert h1 != h2


# ── Edge cases ───────────────────────────────────────────────

def test_empty_password():
    h = hash_password("")
    assert verify_password("", h)


def test_whitespace_password():
    h = hash_password("   ")
    assert not verify_password("", h)
    assert verify_password("   ", h)


def test_unicode_password():
    senha = "çãéñüöß😀"
    h = hash_password(senha)
    assert verify_password(senha, h)


def test_very_long_password():
    senha = "a" * 1000
    h = hash_password(senha)
    assert verify_password(senha, h)


def test_verify_none_hash():
    with pytest.raises((TypeError, ValueError, AttributeError)):
        verify_password("senha", None)


def test_verify_empty_hash():
    with pytest.raises((ValueError, TypeError)):
        verify_password("senha", "")


def test_hash_twice_different():
    h1 = hash_password("abc")
    h2 = hash_password("abc")
    assert h1 != h2
