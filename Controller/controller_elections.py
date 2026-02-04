"""
Election Controller - handles election management business logic.
"""
from datetime import date, datetime
from Models.model_db import Database

# Singleton database instance for controller
_db = Database()


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def _validate_election_dates(start_date, end_date) -> tuple[bool, str | None]:
    today = date.today()
    start = _parse_date(start_date)
    end = _parse_date(end_date)

    if start and start < today:
        return False, "Start date cannot be before today."
    if end and end < today:
        return False, "End date cannot be before today."
    if start and end and end < start:
        return False, "End date cannot be earlier than start date."
    return True, None


def _expected_status(start_date, end_date):
    today = date.today()
    start = _parse_date(start_date)
    end = _parse_date(end_date)

    if start and today < start:
        return "upcoming"
    if end and today > end:
        return "finalized"
    if start and end and start <= today <= end:
        return "active"
    if start and not end and today >= start:
        return "active"
    if end and not start:
        return "active" if today <= end else "finalized"
    return None


def list_elections():
    """Return elections with candidate counts."""
    return _db.get_all_elections()


def list_candidates():
    """Return all candidates (with election_id if already assigned)."""
    return _db.get_all_candidates()


def create_election(data: dict) -> tuple[bool, str]:
    """Create a new election."""
    ok, msg = _validate_election_dates(data.get("start_date"), data.get("end_date"))
    if not ok:
        return False, msg

    status = _expected_status(data.get("start_date"), data.get("end_date")) or data.get("status", "upcoming")
    return _db.create_election(
        title=data.get("title"),
        description=data.get("description", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        status=status,
        allowed_grade=data.get("allowed_grade"),
        allowed_section=data.get("allowed_section", "ALL"),
    )


def update_election(election_id: int, data: dict) -> tuple[bool, str]:
    """Update election details."""
    ok, msg = _validate_election_dates(data.get("start_date"), data.get("end_date"))
    if not ok:
        return False, msg

    status = data.get("status")
    expected = _expected_status(data.get("start_date"), data.get("end_date"))
    if expected and status and status != expected:
        status = expected
    return _db.update_election(
        election_id=election_id,
        title=data.get("title"),
        description=data.get("description", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        status=status,
        allowed_grade=data.get("allowed_grade"),
        allowed_section=data.get("allowed_section", "ALL"),
    )


def delete_election(election_id: int) -> tuple[bool, str]:
    """Deleting elections is disabled to preserve referential integrity."""
    return False, "Deleting elections is disabled. Set status to finalized instead."


def set_election_status(election_id: int, status: str, force: bool = False) -> tuple[bool, str]:
    """Update election status."""
    election = _db.get_election_by_id(election_id)
    if not election:
        return False, "Election not found."

    status = (status or "").strip().lower()
    if status == "ended":
        status = "finalized"
    expected = _expected_status(election.get('start_date'), election.get('end_date'))
    if expected and status != expected and not force:
        if status == "active":
            return False, "Cannot set to Active outside the election date range."
        if status in ("finalized", "ended"):
            return False, "Cannot set to Ended before the election end date."
        if status == "upcoming":
            return False, "Cannot set to Upcoming once the election has started."
        return False, "Election status must match the configured dates."
    return _db.update_election(
        election_id,
        title=election['title'],
        description=election.get('description', ''),
        start_date=election.get('start_date'),
        end_date=election.get('end_date'),
        status=status,
        allowed_grade=election.get('allowed_grade'),
        allowed_section=election.get('allowed_section', 'ALL'),
        status_locked=True
    )


def get_election_by_id(election_id: int) -> dict | None:
    """Get a single election by ID."""
    return _db.get_election_by_id(election_id)


def get_election_results(election_id: int = None) -> dict:
    """Get election results."""
    return _db.get_election_results(election_id)


def get_election_results_by_position(election_id: int) -> dict:
    """Get election results grouped by position."""
    return _db.get_election_results_by_position(election_id)


def get_admin_stats() -> dict:
    """Get admin dashboard statistics."""
    return _db.get_admin_stats()


def get_recent_activity(limit: int | None = 5) -> list[dict]:
    """Get recent audit activity."""
    return _db.get_recent_activity(limit)


def get_dashboard_chart_data(mode: str = "results") -> dict:
    """Get chart data for admin dashboard."""
    return _db.get_dashboard_chart_data(mode=mode)


def get_election_chart_data(election_id: int, mode: str = "results") -> dict:
    """Get chart data for a specific election (used by dashboard filter)."""
    return _db.get_election_chart_data(election_id=election_id, mode=mode)


# === Position management ===
def get_positions_for_election(election_id: int) -> list[dict]:
    """Get all positions for an election."""
    return _db.get_positions_for_election(election_id)


def create_position(election_id: int, title: str, display_order: int = 0) -> tuple[bool, str, int | None]:
    """Create a new position for an election."""
    return _db.create_position(election_id, title, display_order)


def update_position(position_id: int, title: str, display_order: int = None) -> tuple[bool, str]:
    """Update a position."""
    return _db.update_position(position_id, title, display_order)


def delete_position(position_id: int) -> tuple[bool, str]:
    """Delete a position."""
    return _db.delete_position(position_id)


def get_election_ballot_data(election_id: int) -> dict:
    """Get complete ballot data for an election (positions with candidates)."""
    return _db.get_election_ballot_data(election_id)


def assign_candidate_to_position(candidate_id: int, position_id: int) -> tuple[bool, str]:
    """Assign a candidate to a position."""
    return _db.assign_candidate_to_position(candidate_id, position_id)
