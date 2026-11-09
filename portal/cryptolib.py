"""Small crypto helpers used by the deliberately weak Phase 5b challenges.

Everything in here is intentionally misused elsewhere in the app (weak signing
secret, hardcoded symmetric key, ECB mode). The helpers themselves are ordinary;
the lesson is in *how* they are used. Do not copy these call sites into real code.
"""
import base64
import hashlib
import hmac
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# --- base64url helpers -------------------------------------------------------
def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


# --- minimal HS256 JWT -------------------------------------------------------
# A hand-rolled JWT so the lab has no extra dependency. The signing is real
# HMAC-SHA256; the weakness is only ever the *secret* chosen at the call site.
def jwt_encode(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(_b64url_encode(signature))
    return ".".join(segments)


def jwt_decode(token: str, secret: str) -> dict:
    """Verify an HS256 token and return its payload, or raise ValueError."""
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("malformed token") from exc
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(signature_b64)):
        raise ValueError("bad signature")
    return json.loads(_b64url_decode(payload_b64))


# --- AES helpers -------------------------------------------------------------
def aes_cbc_decrypt_b64(key: bytes, blob_b64: str) -> bytes:
    """Decrypt base64(IV || ciphertext) with AES-CBC and strip PKCS#7 padding."""
    raw = base64.b64decode(blob_b64)
    iv, ciphertext = raw[:16], raw[16:]
    return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext), 16)


def aes_ecb_encrypt(key: bytes, data: bytes) -> bytes:
    """Encrypt with AES in ECB mode. Identical plaintext blocks -> identical
    ciphertext blocks: that structure leak is the whole Phase 5b ECB lesson."""
    return AES.new(key, AES.MODE_ECB).encrypt(pad(data, 16))
