"""SMS notification sending.

Imports shared.validation for phone number validation.
"""

from shared.validation import validate_phone

_sms_log = []
_next_id = 1


def send_sms(phone, message):
    """Send an SMS after validating the phone number."""
    global _next_id
    if not validate_phone(phone):
        return {"success": False, "error": "Invalid phone number"}
    msg = _truncate_message(message)
    status = {
        "success": True,
        "phone": _format_phone(phone),
        "message_id": f"sms-{_next_id:04d}",
        "length": len(msg),
    }
    _sms_log.append(status)
    _next_id += 1
    return status


def _truncate_message(message, max_len=160):
    """Truncate message to SMS length limit."""
    if len(message) <= max_len:
        return message
    return message[: max_len - 3] + "..."


def _format_phone(phone):
    """Normalise phone number to +61 format."""
    cleaned = phone.replace(" ", "")
    if cleaned.startswith("0"):
        return "+61" + cleaned[1:]
    return cleaned


def get_delivery_status(message_id):
    """Look up delivery status for a sent message."""
    for entry in _sms_log:
        if entry.get("message_id") == message_id:
            return "delivered"
    return "not_found"

# --- Added by Agent D: Rate-limited SMS sending ---
def send_sms_rated(phone, message):
    from notifications.email_sender import _rate_limiter
    if not _rate_limiter.allow(): return {"success": False, "error": "Rate limit exceeded"}
    return send_sms(phone, message)
