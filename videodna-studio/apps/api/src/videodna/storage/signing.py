"""HMAC-signed tokens for local-storage URLs (the S3 backend uses presigned URLs)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class InvalidToken(Exception):
    pass


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def sign(payload: dict[str, Any], secret: str, ttl_sec: int) -> str:
    body = dict(payload, exp=int(time.time()) + ttl_sec)
    raw = _b64(json.dumps(body, separators=(",", ":"), sort_keys=True).encode())
    mac = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest()
    return f"{raw}.{_b64(mac)}"


def verify(token: str, secret: str) -> dict[str, Any]:
    try:
        raw, mac = token.split(".", 1)
    except ValueError as exc:
        raise InvalidToken("malformed") from exc
    expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64(mac)):
        raise InvalidToken("bad signature")
    payload = json.loads(_unb64(raw))
    if int(payload.get("exp", 0)) < time.time():
        raise InvalidToken("expired")
    return payload
