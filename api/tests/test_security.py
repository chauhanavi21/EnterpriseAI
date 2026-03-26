"""
Unit tests for security module: password hashing, JWT token creation/verification.
"""
import pytest
from datetime import timedelta
from unittest.mock import patch

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    """Test bcrypt password hashing and verification."""

    @pytest.mark.unit
    def test_hash_password_returns_hash(self):
        hashed = hash_password("MySecretPassword1!")
        assert hashed != "MySecretPassword1!"
        assert len(hashed) > 20

    @pytest.mark.unit
    def test_verify_password_correct(self):
        password = "CorrectHorseBatteryStaple"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        hashed = hash_password("RealPassword")
        assert verify_password("WrongPassword", hashed) is False

    @pytest.mark.unit
    def test_hash_is_unique_each_time(self):
        """Each hash should be different due to random salt."""
        h1 = hash_password("SamePassword")
        h2 = hash_password("SamePassword")
        assert h1 != h2  # bcrypt uses random salt

    @pytest.mark.edge
    def test_hash_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    @pytest.mark.edge
    def test_hash_very_long_password(self):
        """bcrypt truncates at 72 bytes, but should still work."""
        long_pw = "A" * 100
        hashed = hash_password(long_pw)
        assert verify_password(long_pw, hashed) is True

    @pytest.mark.edge
    def test_hash_unicode_password(self):
        pw = "пароль密码パスワード"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True


class TestJWT:
    """Test JWT access and refresh token creation/decoding."""

    @pytest.mark.unit
    def test_create_access_token(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 20

    @pytest.mark.unit
    def test_decode_access_token(self):
        token = create_access_token("user-456")
        payload = decode_token(token)
        assert payload["sub"] == "user-456"
        assert payload["type"] == "access"

    @pytest.mark.unit
    def test_create_refresh_token(self):
        token = create_refresh_token("user-789")
        payload = decode_token(token)
        assert payload["sub"] == "user-789"
        assert payload["type"] == "refresh"

    @pytest.mark.unit
    def test_token_expiry(self):
        token = create_access_token("user-exp", expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)
        # Expired token should return None
        assert payload is None

    @pytest.mark.edge
    def test_decode_invalid_token(self):
        payload = decode_token("invalid.token.string")
        assert payload is None

    @pytest.mark.edge
    def test_decode_empty_token(self):
        payload = decode_token("")
        assert payload is None

    @pytest.mark.edge
    def test_token_with_special_chars_in_subject(self):
        sub = "user@example.com|org:123"
        token = create_access_token(sub)
        payload = decode_token(token)
        assert payload["sub"] == sub
