"""
Election Controller - handles election management business logic.
"""
from Models.model_db import Database

# Singleton database instance for controller
_db = Database()


def list_elections():
    """Return elections with candidate counts."""
    return _db.get_all_elections()


def list_candidates():
    """Return all candidates (with election_id if already assigned)."""
    return _db.get_all_candidates()


def create_election(data: dict) -> tuple[bool, str]:
    """Create a new election."""
    return _db.create_election(
        title=data.get("title"),
        description=data.get("description", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        status=data.get("status", "upcoming"),
        allowed_grade=data.get("allowed_grade"),
        allowed_section=data.get("allowed_section", "ALL"),
    )


def update_election(election_id: int, data: dict) -> tuple[bool, str]:
    """Update election details."""
    return _db.update_election(
        election_id=election_id,
        title=data.get("title"),
        description=data.get("description", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        status=data.get("status"),
        allowed_grade=data.get("allowed_grade"),
        allowed_section=data.get("allowed_section", "ALL"),
    )


def delete_election(election_id: int) -> tuple[bool, str]:
    """Deleting elections is disabled to preserve referential integrity."""
    return False, "Deleting elections is disabled. Set status to finalized instead."


def set_election_status(election_id: int, status: str) -> tuple[bool, str]:
    """Update election status."""
    election = _db.get_election_by_id(election_id)
    if not election:
        return False, "Election not found."
    return _db.update_election(
        election_id,
        title=election['title'],
        description=election.get('description', ''),
        start_date=election.get('start_date'),
        end_date=election.get('end_date'),
        status=status,
        allowed_grade=election.get('allowed_grade'),
        allowed_section=election.get('allowed_section', 'ALL')
    )


def get_election_by_id(election_id: int) -> dict | None:
    """Get a single election by ID."""
    return _db.get_election_by_id(election_id)


def get_election_results(election_id: int = None) -> dict:
    """Get election results."""
    return _db.get_election_results(election_id)


def get_admin_stats() -> dict:
    """Get admin dashboard statistics."""
    return _db.get_admin_stats()


def get_recent_activity(limit: int = 5) -> list[dict]:
    """Get recent voting activity."""
    return _db.get_recent_activity(limit)


def get_dashboard_chart_data() -> dict:
    """Get chart data for admin dashboard."""
    return _db.get_dashboard_chart_data()
