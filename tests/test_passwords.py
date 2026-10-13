from auth.passwords import hash_password, verify_password
import pytest

def test_password_hash_round_trip():
    raw = "correct-horse-battery-2026"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("wrong-password", hashed)

def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password("short")
