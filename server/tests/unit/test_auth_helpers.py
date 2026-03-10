from __future__ import annotations

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    password_hash = hash_password("pass123")
    assert verify_password("pass123", password_hash)


def test_wrong_password_fails() -> None:
    password_hash = hash_password("pass123")
    assert not verify_password("wrong-pass", password_hash)


def test_access_token_payload_contains_access_type() -> None:
    token, _ = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["token_type"] == "access"


def test_refresh_token_payload_contains_refresh_type() -> None:
    token, _ = create_refresh_token("user-123")
    payload = decode_token(token)
    assert payload["token_type"] == "refresh"
