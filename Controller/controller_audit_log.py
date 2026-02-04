"""
Audit Log Controller - handles audit log retrieval for UI layers.
"""
from Models.model_db import Database

# Singleton database instance for controller
_db = Database()


def get_recent_activity(limit: int | None = 5) -> list[dict]:
    """Get recent audit activity."""
    return _db.get_recent_activity(limit)


def get_audit_logs(limit: int | None = 10) -> list[dict]:
    """Get audit logs (alias for recent activity)."""
    return _db.get_audit_logs(limit)
