"""
Voter Controller - handles voter management business logic.
"""
from Models.model_db import Database
from Models.base import get_connection

# Singleton database instance for controller
_db = Database()


def list_voters_with_status() -> list[dict]:
    """Return all voters with their voting status."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    # Consider any vote across elections; show latest vote time if multiple
    cursor.execute("""
        SELECT u.*, vr_latest.voted_at
        FROM users u
        LEFT JOIN (
            SELECT user_id, MAX(voted_at) AS voted_at
            FROM voting_records
            GROUP BY user_id
        ) vr_latest ON vr_latest.user_id = u.user_id
        WHERE u.role = 'student'
        ORDER BY u.full_name
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def create_voter(data: dict) -> tuple[bool, str]:
    """Create a new voter (student)."""
    return _db.create_voter(
        full_name=data.get("full_name"),
        email=data.get("email"),
        student_id=data.get("student_id"),
        password=data.get("password"),
        grade_level=data.get("grade_level"),
        section=data.get("section"),
    )


def update_voter(user_id: int, data: dict) -> tuple[bool, str]:
    """Update voter information."""
    return _db.update_voter(
        user_id=user_id,
        full_name=data.get("full_name"),
        email=data.get("email"),
        student_id=data.get("student_id"),
        grade_level=data.get("grade_level"),
        section=data.get("section"),
    )


def delete_voter(user_id: int) -> tuple[bool, str]:
    """Delete a voter."""
    return _db.delete_voter(user_id)


def voter_stats() -> dict:
    """Get voter statistics."""
    return _db.get_voter_stats()


def list_sections() -> list[dict]:
    """Get all sections."""
    return _db.get_sections()


def add_section(grade_level: int, section_name: str) -> tuple[bool, str]:
    """Add a new section."""
    return _db.create_section(grade_level, section_name)


def get_user_by_id(user_id: int) -> dict | None:
    """Get user details by ID."""
    return _db.get_user_by_id(user_id)


def update_user_profile(user_id: int, full_name: str, email: str, student_id: str,
                        new_password: str | None = None) -> tuple[bool, str]:
    """Update user profile."""
    return _db.update_user_profile(user_id, full_name, email, student_id, new_password)


def get_user_voting_history(user_id: int) -> list[dict]:
    """Get voting history for a user."""
    return _db.get_user_voting_history(user_id)


def has_user_voted(user_id: int, election_id: int) -> bool:
    """Check if user has voted in an election."""
    return _db.has_user_voted(user_id, election_id)


def cast_vote(user_id: int, election_id: int, candidate_id: int) -> tuple[bool, str]:
    """Cast a vote."""
    return _db.cast_vote(user_id, election_id, candidate_id)
