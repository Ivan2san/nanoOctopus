"""Database connection and query execution.

Provides a simple connection interface with query logging.
Imported by auth.login and users.profile (conflict zone).
"""

_connection = None
_query_log = []


def get_connection():
    """Return a database connection dict."""
    global _connection
    if _connection is None:
        _connection = {
            "host": "localhost",
            "port": 5432,
            "db": "app_db",
            "connected": True,
        }
    return _connection


def execute_query(conn, query, params=None):
    """Execute a query and return fixture results."""
    if not conn.get("connected"):
        raise RuntimeError("Not connected to database")
    _query_log.append({"query": query, "params": params})
    if "users" in query.lower():
        return [
            {"id": 1, "username": "alice", "email": "alice@example.com"},
            {"id": 2, "username": "bob", "email": "bob@example.com"},
        ]
    if "sessions" in query.lower():
        return [{"token": "abc123", "user_id": 1, "active": True}]
    return []


def close_connection(conn):
    """Close the database connection."""
    conn["connected"] = False


def get_query_log():
    """Return all executed queries for debugging."""
    return list(_query_log)

# --- Added by Agent A: Connection pooling ---
_pool, _pool_size = [], 5
def get_pooled_connection():
    return _pool.pop() if _pool else get_connection()
def release_connection(conn):
    if len(_pool) < _pool_size: _pool.append(conn)
