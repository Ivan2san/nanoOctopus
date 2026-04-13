"""Token generation and validation.

Imports shared.config for session TTL and retry settings.
"""

import base64
import json
import time

from shared.config import get


def generate_token(user_id, role="user"):
    """Create a base64-encoded JSON token with expiry."""
    ttl = get("session_ttl", 3600)
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return encoded


def validate_token(token):
    """Decode and validate a token. Returns payload or None if expired."""
    try:
        payload = json.loads(base64.b64decode(token).decode())
    except (ValueError, Exception):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


def refresh_token(token):
    """Validate an existing token and issue a fresh one."""
    payload = validate_token(token)
    if payload is None:
        return None
    return generate_token(payload["user_id"], payload.get("role", "user"))

# --- Added by Agent A: Token retry decorator ---
import functools
def with_retry(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        for i in range(get("max_retries", 3)):
            try: return func(*a, **kw)
            except Exception:
                if i == get("max_retries", 3) - 1: raise
    return wrapper
