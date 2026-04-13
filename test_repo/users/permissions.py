"""Role-based permission management.

Imports shared.validation for input sanitisation.
"""

from shared.validation import sanitise_string

ROLES = {
    "admin": {"read", "write", "delete", "manage_users"},
    "editor": {"read", "write"},
    "viewer": {"read"},
    "guest": set(),
}


def check_permission(user_role, action):
    """Check whether a role has a specific permission."""
    permissions = ROLES.get(user_role, set())
    return action in permissions


def assign_role(user_id, role):
    """Assign a role to a user after sanitising the role name."""
    clean_role = sanitise_string(role).lower()
    if clean_role not in ROLES:
        return False
    return True


def get_permissions(role):
    """Return the permission set for a given role."""
    return set(ROLES.get(role, set()))


def list_roles():
    """Return all available role names."""
    return sorted(ROLES.keys())

# --- Added by Agent B: Role name validation ---
def validate_role_name(role):
    from shared.validation import validate_length
    clean = sanitise_string(role)
    return clean == role and validate_length(role, 2, 32)
