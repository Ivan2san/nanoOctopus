"""Email notification sending.

Standalone module with no shared imports.
"""

from email.mime.text import MIMEText

_email_log = []


def send_email(to, subject, body):
    """Send an email (simulated) and return a status dict."""
    message = _build_mime_message(to, subject, body)
    status = {
        "to": to,
        "subject": subject,
        "status": "sent",
        "message_id": f"msg-{len(_email_log) + 1:04d}",
        "mime_length": len(message),
    }
    log_email(status)
    return status


def _build_mime_message(to, subject, body):
    """Construct a MIME text message."""
    msg = MIMEText(body, "plain")
    msg["To"] = to
    msg["Subject"] = subject
    msg["From"] = "notifications@nanoapp.local"
    return msg.as_string()


def _validate_recipients(recipients):
    """Filter out obviously invalid email addresses."""
    return [r for r in recipients if "@" in r and "." in r.split("@")[-1]]


def log_email(status):
    """Append a send status to the email log."""
    _email_log.append(status)


def get_email_log():
    """Return all logged email statuses."""
    return list(_email_log)

# --- Added by Agent D: Rate limiting ---
import time as _time
class RateLimiter:
    def __init__(self, rate=10.0, cap=10.0):
        self.rate, self.cap, self._tokens, self._t = rate, cap, cap, _time.monotonic()
    def allow(self):
        now = _time.monotonic()
        self._tokens = min(self.cap, self._tokens + (now - self._t) * self.rate)
        self._t = now
        if self._tokens >= 1.0: self._tokens -= 1.0; return True
        return False
_rate_limiter = RateLimiter()
