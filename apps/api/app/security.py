"""Password hashing and session-token primitives.

Uses stdlib scrypt (OpenSSL-backed, memory-hard KDF) so the API keeps zero
extra dependencies. Hash format: ``scrypt$N$r$p$salt_hex$hash_hex`` — the
parameters travel with each hash, so cost factors can be raised later
without invalidating existing accounts.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32

SESSION_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_BYTES,
    )
    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}"
        f"${salt.hex()}${derived.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, n_str, r_str, p_str, salt_hex, hash_hex = stored_hash.split("$")
        if scheme != "scrypt":
            return False
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n_str),
            r=int(r_str),
            p=int(p_str),
            dklen=len(bytes.fromhex(hash_hex)),
        )
        return hmac.compare_digest(derived, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    """Opaque browser-held session token (never stored server-side)."""
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """Stored representation of a session token (SHA-256 hex)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
