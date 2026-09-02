from datetime import timedelta
import pytest
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_hash_password_and_verify_correct_password():
    password = "minha_senha_secreta"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_verify_password_with_incorrect_password():
    password = "senha_correta"
    hashed = hash_password(password)

    assert verify_password("senha_errada", hashed) is False


def test_create_and_decode_valid_access_token():
    payload_data = {"sub": "12345", "role": "CLIENT"}
    token = create_access_token(payload_data)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "12345"
    assert decoded["role"] == "CLIENT"
    assert "exp" in decoded


def test_decode_expired_access_token():
    payload_data = {"sub": "12345"}
    # Token criado já expirado no passado
    token = create_access_token(payload_data, expires_delta=timedelta(seconds=-10))

    decoded = decode_access_token(token)
    assert decoded is None


def test_decode_invalid_token():
    assert decode_access_token("token_invalido_qualquer") is None
