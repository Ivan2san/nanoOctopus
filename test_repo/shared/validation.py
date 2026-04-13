"""Input validation utilities.

Provides email, phone, and string validation functions.
Imported by users.permissions and notifications.sms (conflict zone).
"""

import re


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_email(email):
    """Check if email address has a valid format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone):
    """Check if phone number matches AU format (+61 or 04xx)."""
    pattern = r"^(\+61|0)[2-9]\d{8}$"
    return bool(re.match(pattern, phone.replace(" ", "")))


def sanitise_string(value):
    """Strip HTML tags and trim whitespace."""
    cleaned = re.sub(r"<[^>]+>", "", value)
    return cleaned.strip()


def validate_length(value, min_len=1, max_len=255):
    """Check if string length is within bounds."""
    return min_len <= len(value) <= max_len

# --- Added by Agent B: HTML sanitisation ---
DANGEROUS_PATTERNS = [r'<script.*?>', r'javascript:', r'on\w+\s*=']
def sanitise_html(value):
    result = value
    for pat in DANGEROUS_PATTERNS: result = re.sub(pat, '', result, flags=re.IGNORECASE)
    return result
