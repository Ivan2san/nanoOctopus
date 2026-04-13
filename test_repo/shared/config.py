"""Application configuration.

Provides a simple key-value config with defaults and env overrides.
Imported by auth.tokens and reports.export (conflict zone).
"""

import os

_DEFAULTS = {
    "app_name": "NanoApp",
    "version": "1.0.0",
    "debug": False,
    "db_host": "localhost",
    "db_port": 5432,
    "session_ttl": 3600,
    "export_format": "json",
    "max_retries": 3,
}

_config = dict(_DEFAULTS)


def get(key, default=None):
    """Return a config value by key."""
    return _config.get(key, default)


def set(key, value):
    """Update a config value."""
    _config[key] = value


def load_from_env():
    """Load config overrides from NANO_ prefixed env vars."""
    for key in _DEFAULTS:
        env_key = "NANO_" + key.upper()
        if env_key in os.environ:
            _config[key] = os.environ[env_key]
    return dict(_config)


def reset():
    """Restore all config values to defaults."""
    _config.clear()
    _config.update(_DEFAULTS)

# --- Added by Agent A: Pool and retry configuration ---
_config.update({"pool_size": 5, "retry_delay": 0.5, "connection_timeout": 30})
