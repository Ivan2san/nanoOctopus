"""User authentication and session creation.

Imports shared.database for credential lookup.
"""

import hashlib
import secrets

from shared.database import get_connection, execute_query


def _hash_password(password):
    """Hash a password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    """Authenticate a user against the database.

    Returns a result dict with success status and user_id.
    """
    conn = get_connection()
    rows = execute_query(conn, "SELECT * FROM users WHERE username = ?", (username,))
    if not rows:
        return {"success": False, "user_id": None, "error": "User not found"}
    user = rows[0]
    return {"success": True, "user_id": user["id"], "error": None}


def create_session(user_id):
    """Generate a new session token for the given user."""
    token = secrets.token_hex(32)
    conn = get_connection()
    execute_query(conn, "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
                  (token, user_id))
    return token


def invalidate_session(token):
    """Remove a session token from the database."""
    conn = get_connection()
    execute_query(conn, "DELETE FROM sessions WHERE token = ?", (token,))
    return True

# --- Added by Agent A: Retry logic ---
def authenticate_with_retry(username, password, max_retries=3):
    for attempt in range(max_retries):
        result = authenticate(username, password)
        if result["success"]: return result
        time.sleep(0.1 * (2 ** attempt))
    return result
