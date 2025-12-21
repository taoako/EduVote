"""
Candidate Controller - handles candidate management business logic.
"""
from Models.model_db import Database
from Models.base import get_connection

# Singleton database instance for controller
_db = Database()


def list_elections_options():
    """Return only upcoming or active elections for candidate assignment."""
    elections = _db.get_all_elections()
    return [e for e in elections if (e.get('status') or '').lower() in ('upcoming', 'active')]


def list_candidates():
    """Return all candidates with election info."""
    return _db.get_all_candidates()


def get_candidates_for_election(election_id: int) -> list[dict]:
    """Return candidates for a specific election.

    Uses raw SQL to include optional columns (position/bio/email/phone/platform)
    when they exist in the legacy schema.
    """
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)

        optional_cols = []
        for col in ("position", "bio", "email", "phone", "platform"):
            if _has_column("candidates", col):
                optional_cols.append(col)

        select_cols = [
            "candidate_id",
            "election_id",
            "user_id",
            "full_name",
            "slogan",
            "photo_path",
            "vote_count",
        ] + optional_cols

        cursor.execute(
            f"SELECT {', '.join(select_cols)} FROM candidates WHERE election_id = %s ORDER BY full_name",
            (election_id,),
        )
        rows = cursor.fetchall() or []
        cursor.close()
        conn.close()
        return rows
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return []


def _has_column(table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return False


def create_candidate(data: dict) -> tuple[bool, str]:
    """Create a new candidate, optionally linked to multiple elections."""
    conn = get_connection()
    if not conn:
        return False, "Database connection failed"
    try:
        cursor = conn.cursor()
        
        # Fetch user name to store denormalized full_name for display
        user_id = data.get("user_id")
        user_name = None
        if user_id:
            cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return False, "Selected user not found"
            user_name = row[0]

        election_ids = data.get("election_ids") or []
        if not election_ids:
            cursor.close()
            conn.close()
            return False, "Select at least one election"

        # Check for optional columns
        has_position = _has_column("candidates", "position")
        has_bio = _has_column("candidates", "bio")
        has_email = _has_column("candidates", "email")
        has_phone = _has_column("candidates", "phone")
        has_platform = _has_column("candidates", "platform")

        optional_cols = []
        optional_vals = []
        if has_position:
            optional_cols.append("position")
            optional_vals.append(data.get("position"))
        if has_bio:
            optional_cols.append("bio")
            optional_vals.append(data.get("bio"))
        if has_email:
            optional_cols.append("email")
            optional_vals.append(data.get("email"))
        if has_phone:
            optional_cols.append("phone")
            optional_vals.append(data.get("phone"))
        if has_platform:
            optional_cols.append("platform")
            optional_vals.append(data.get("platform"))

        base_cols = ["full_name", "slogan", "photo_path", "election_id", "user_id", "vote_count"]
        base_vals = [user_name or data.get("full_name"), data.get("slogan"), data.get("photo_path"), None, user_id, 0]

        col_sql = base_cols + optional_cols
        placeholders = ["%s"] * len(col_sql)

        for eid in election_ids:
            base_vals[3] = eid
            cursor.execute(
                f"INSERT INTO candidates ({', '.join(col_sql)}) VALUES ({', '.join(placeholders)})",
                base_vals + optional_vals,
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Candidate created"
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return False, f"Failed to add candidate: {e}"


def update_candidate(candidate_id: int, data: dict) -> tuple[bool, str]:
    """Update an existing candidate."""
    conn = get_connection()
    if not conn:
        return False, "Database connection failed"
    try:
        cursor = conn.cursor()
        user_id = data.get("user_id")
        user_name = None
        if user_id:
            cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return False, "Selected user not found"
            user_name = row[0]

        election_ids = data.get("election_ids") or []
        if not election_ids:
            cursor.close()
            conn.close()
            return False, "Select at least one election"

        # Detect optional columns
        has_position = _has_column("candidates", "position")
        has_bio = _has_column("candidates", "bio")
        has_email = _has_column("candidates", "email")
        has_phone = _has_column("candidates", "phone")
        has_platform = _has_column("candidates", "platform")

        optional_cols = []
        optional_vals = []
        if has_position:
            optional_cols.append("position")
            optional_vals.append(data.get("position"))
        if has_bio:
            optional_cols.append("bio")
            optional_vals.append(data.get("bio"))
        if has_email:
            optional_cols.append("email")
            optional_vals.append(data.get("email"))
        if has_phone:
            optional_cols.append("phone")
            optional_vals.append(data.get("phone"))
        if has_platform:
            optional_cols.append("platform")
            optional_vals.append(data.get("platform"))

        set_clauses = ["full_name=%s", "slogan=%s", "photo_path=%s", "election_id=%s", "user_id=%s"]
        values = [user_name or data.get("full_name"), data.get("slogan"), data.get("photo_path"), election_ids[0], user_id]

        for col in optional_cols:
            set_clauses.append(f"{col}=%s")
        values.extend(optional_vals)
        values.append(candidate_id)

        cursor.execute(
            f"UPDATE candidates SET {', '.join(set_clauses)} WHERE candidate_id=%s",
            values,
        )

        # For any additional elections, insert new rows for the same user
        extra = election_ids[1:]
        for eid in extra:
            base_vals = [user_name or data.get("full_name"), data.get("slogan"), data.get("photo_path"), eid, user_id, 0]
            col_sql = ["full_name", "slogan", "photo_path", "election_id", "user_id", "vote_count"] + optional_cols
            placeholders = ["%s"] * len(col_sql)
            cursor.execute(
                f"INSERT INTO candidates ({', '.join(col_sql)}) VALUES ({', '.join(placeholders)})",
                base_vals + optional_vals,
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Candidate updated"
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return False, f"Failed to update candidate: {e}"


def delete_candidate(candidate_id: int) -> tuple[bool, str]:
    """Delete a candidate."""
    return _db.delete_candidate(candidate_id)


def list_candidate_users():
    """Return list of student users who can be candidates."""
    return _db.list_student_users()
