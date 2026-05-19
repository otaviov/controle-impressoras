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
