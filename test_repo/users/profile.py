"""User profile management.

Imports shared.database for profile queries.
"""

from shared.database import get_connection, execute_query


def get_profile(user_id):
    """Fetch a user profile by ID."""
    conn = get_connection()
    rows = execute_query(conn, "SELECT * FROM users WHERE id = ?", (user_id,))
    if not rows:
        return None
    return rows[0]


def update_profile(user_id, **fields):
    """Update profile fields for the given user."""
    if not fields:
        return False
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = tuple(fields.values()) + (user_id,)
    execute_query(conn, f"UPDATE users SET {set_clause} WHERE id = ?", params)
    return True


def delete_profile(user_id):
    """Soft-delete a user profile by setting active to False."""
    return update_profile(user_id, active=False)


def _format_display_name(first, last):
    """Format a display name from first and last names."""
    parts = [p.strip() for p in (first, last) if p and p.strip()]
    return " ".join(parts)

# --- Added by Agent B: Profile field sanitisation ---
def sanitise_profile_fields(profile):
    from shared.validation import sanitise_string
    return {k: sanitise_string(v) if isinstance(v, str) else v for k, v in profile.items()}
