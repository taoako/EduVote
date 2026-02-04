"""
Database Service Layer - provides business logic operations using SQLAlchemy ORM models.

Moved out of Models to keep ORM models isolated. Controllers should use this class
for all database operations.
"""
import hashlib

try:
    import bcrypt as py_bcrypt
except Exception:  # pragma: no cover
    py_bcrypt = None
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError
from Models.base import get_session, init_db, get_connection
from Models.model_user import User
from Models.model_election import Election
from Models.model_candidate import Candidate
from Models.model_section import Section
from Models.model_voting_record import VotingRecord
from Models.model_position import Position
from Models.model_audit_log import AuditLog


class Database:
    def _normalize_date(self, value):
        if value is None:
            return None
        try:
            from datetime import date, datetime
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
                return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            return None
        return None

    def _compute_status_from_dates(self, start_date, end_date, today=None):
        from datetime import date

        today = today or date.today()
        start = self._normalize_date(start_date)
        end = self._normalize_date(end_date)

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

    def _sync_election_statuses(self, session, elections):
        from datetime import date

        today = date.today()
        changed = False
        for e in elections:
            if bool(getattr(e, "status_locked", False)):
                continue
            new_status = self._compute_status_from_dates(e.start_date, e.end_date, today)
            if new_status and e.status != new_status:
                e.status = new_status
                changed = True
        if changed:
            session.commit()

    def _sync_all_elections(self, session):
        elections = session.query(Election).all()
        self._sync_election_statuses(session, elections)
    """
    Service layer that provides data access operations using SQLAlchemy ORM.
    Controllers should use this class for all database operations.
    """
    
    def __init__(self):
        # Initialize database schema on first Database instance
        init_db()

    def _log_audit(self, session, action: str, details: str | None = None, user_id: int | None = None):
        """Insert an audit log record using an existing session."""
        try:
            safe_action = (action or "Activity").strip()[:128]
            log = AuditLog(user_id=user_id, action=safe_action, details=details)
            session.add(log)
        except Exception:
            # Do not block main flow on audit logging failures
            pass
    
    # === Connection methods (legacy support) ===
    def get_connection(self):
        """Legacy: Get raw MySQL connection for complex queries."""
        return get_connection()

    def get_audit_logs(self, limit: int | None = 10) -> list[dict]:
        """Get recent audit logs for admin visibility."""
        session = get_session()
        try:
            query = session.query(AuditLog).outerjoin(User, User.user_id == AuditLog.user_id).order_by(
                AuditLog.created_at.desc()
            )
            if limit is not None:
                query = query.limit(limit)
            logs = query.all()

            # If no audit logs yet, fallback to voting records so the panel isn't empty.
            if not logs:
                vr_query = session.query(VotingRecord).join(User).join(Election).order_by(
                    VotingRecord.voted_at.desc()
                )
                if limit is not None:
                    vr_query = vr_query.limit(limit)
                records = vr_query.all()

                fallback = []
                for r in records:
                    user_name = r.user.full_name if r.user else "System"
                    election_title = r.election.title if r.election else "Election"
                    candidate_name = r.candidate.full_name if getattr(r, "candidate", None) else None
                    status = (r.status or "").lower()

                    if status == "spoiled" or r.candidate_id is None:
                        action = "Abstained"
                        details = f"Abstained from voting in {election_title}"
                    else:
                        action = "Vote cast"
                        details = f"Voted in {election_title}"
                        if candidate_name:
                            details = f"Voted for {candidate_name} in {election_title}"

                    fallback.append({
                        "action": action,
                        "details": details,
                        "created_at": r.voted_at,
                        "user_name": user_name,
                    })

                return fallback

            result = []
            for log in logs:
                user_name = None
                try:
                    if getattr(log, "user", None) is not None:
                        user_name = log.user.full_name
                except Exception:
                    user_name = None
                result.append({
                    "action": log.action,
                    "details": log.details,
                    "created_at": log.created_at,
                    "user_name": user_name or "System",
                })
            return result
        finally:
            session.close()
    
    # === User methods ===
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _verify_password(password: str, stored_hash: str | None) -> bool:
        """Verify a plaintext password against either SHA-256 hex or bcrypt hashes."""
        if not stored_hash:
            return False

        stored = stored_hash.strip()
        if stored.startswith("$2"):
            if py_bcrypt is None:
                return False
            try:
                # MariaDB/phpMyAdmin dumps often use "$2y$" prefix; python bcrypt expects "$2b$".
                normalized = stored
                if normalized.startswith("$2y$"):
                    normalized = "$2b$" + normalized[4:]

                return bool(
                    py_bcrypt.checkpw(
                        password.encode("utf-8"),
                        normalized.encode("utf-8"),
                    )
                )
            except Exception:
                return False

        return Database.hash_password(password) == stored
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        session = get_session()
        try:
            exists = session.query(User).filter(User.username == username.strip()).first() is not None
            return exists
        finally:
            session.close()
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        session = get_session()
        try:
            exists = session.query(User).filter(User.email == email.strip().lower()).first() is not None
            return exists
        finally:
            session.close()
    
    def student_id_exists(self, student_id: str) -> bool:
        """Check if student ID already exists."""
        session = get_session()
        try:
            exists = session.query(User).filter(User.student_id == student_id.strip()).first() is not None
            return exists
        finally:
            session.close()
    
    def register_user(self, full_name: str, email: str, student_id: str, password: str,
                      grade_level=None, section=None) -> tuple[bool, str]:
        """Register a new user."""
        session = get_session()
        try:
            # Check for existing email or student_id
            if session.query(User).filter(User.email == email.strip().lower()).first():
                return False, "Email already registered."
            if session.query(User).filter(User.student_id == student_id.strip()).first():
                return False, "Student ID already registered."
            
            # Create username from student_id
            username = student_id.strip()
            
            user = User(
                username=username,
                password_hash=self.hash_password(password),
                full_name=full_name.strip(),
                student_id=student_id.strip(),
                email=email.strip().lower(),
                role='student',
                grade_level=grade_level,
                section=section
            )
            session.add(user)
            session.flush()
            self._log_audit(
                session,
                "Voter registered",
                f"{user.full_name} ({user.student_id}) registered",
                user.user_id,
            )
            session.commit()
            return True, "Registration successful!"
        except IntegrityError as e:
            session.rollback()
            return False, f"Registration failed: {str(e)}"
        except Exception as e:
            session.rollback()
            return False, f"Registration failed: {str(e)}"
        finally:
            session.close()
    
    def authenticate_user(self, username: str, student_id: str, password: str) -> tuple[bool, dict | None]:
        """Authenticate a user by username/student_id and password."""
        session = get_session()
        try:
            user = session.query(User).filter(
                or_(
                    User.username == username.strip(),
                    User.student_id == student_id.strip(),
                )
            ).first()

            if user and self._verify_password(password, user.password_hash):
                self._log_audit(
                    session,
                    "Login",
                    f"{user.full_name} logged in",
                    user.user_id,
                )
                return True, user.to_dict()
            return False, None
        finally:
            session.close()

    def reset_password(self, student_id: str, email: str, new_password: str) -> tuple[bool, str]:
        """Reset a user's password by verifying student_id + email."""
        session = get_session()
        try:
            sid = (student_id or "").strip()
            em = (email or "").strip().lower()
            if not sid or not em or not new_password:
                return False, "Missing required information."

            user = session.query(User).filter(
                and_(User.student_id == sid, func.lower(User.email) == em)
            ).first()
            if not user:
                return False, "No account matches that Student ID and email."

            user.password_hash = self.hash_password(new_password)
            self._log_audit(
                session,
                "Password reset",
                f"Password reset for {user.full_name} ({user.student_id})",
                user.user_id,
            )
            session.commit()
            return True, "Password reset successfully. You can now log in."
        except Exception as e:
            session.rollback()
            return False, f"Password reset failed: {str(e)}"
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> dict | None:
        """Get user by ID."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            return user.to_dict() if user else None
        finally:
            session.close()
    
    def update_user_profile(self, user_id: int, full_name: str, email: str, student_id: str,
                            new_password: str | None = None) -> tuple[bool, str]:
        """Update user profile."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False, "User not found."
            
            # Check for duplicate email/student_id
            if email.strip().lower() != user.email:
                if session.query(User).filter(User.email == email.strip().lower()).first():
                    return False, "Email already in use."
            
            if student_id.strip() != user.student_id:
                if session.query(User).filter(User.student_id == student_id.strip()).first():
                    return False, "Student ID already in use."
            
            user.full_name = full_name.strip()
            user.email = email.strip().lower()
            user.student_id = student_id.strip()
            user.username = student_id.strip()  # Keep username synced

            self._log_audit(
                session,
                "Profile updated",
                f"Profile updated for {user.full_name} ({user.student_id})",
                user.user_id,
            )
            
            if new_password:
                user.password_hash = self.hash_password(new_password)
            
            session.commit()
            return True, "Profile updated successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Update failed: {str(e)}"
        finally:
            session.close()
    
    def list_student_users(self) -> list[dict]:
        """Get all students."""
        session = get_session()
        try:
            users = session.query(User).filter(User.role == 'student').all()
            return [u.to_dict() for u in users]
        finally:
            session.close()
    
    def get_all_voters(self) -> list[dict]:
        """Get all voters with voting stats."""
        session = get_session()
        try:
            users = session.query(User).filter(User.role == 'student').all()
            result = []
            for u in users:
                user_dict = u.to_dict()
                user_dict['votes_cast'] = len(u.votes)
                result.append(user_dict)
            return result
        finally:
            session.close()
    
    def get_voter_stats(self) -> dict:
        """Get voter statistics."""
        session = get_session()
        try:
            total = session.query(func.count(User.user_id)).filter(User.role == 'student').scalar() or 0
            active = session.query(func.count(func.distinct(VotingRecord.user_id))).scalar() or 0
            return {'total_voters': total, 'active_voters': active}
        finally:
            session.close()
    
    def create_voter(self, full_name: str, email: str, student_id: str, password: str,
                     grade_level=None, section=None) -> tuple[bool, str]:
        """Create a new voter (alias for register_user)."""
        return self.register_user(full_name, email, student_id, password, grade_level, section)
    
    def update_voter(self, user_id: int, full_name: str, email: str, student_id: str,
                     grade_level=None, section=None) -> tuple[bool, str]:
        """Update voter information."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False, "User not found."
            
            user.full_name = full_name.strip()
            user.email = email.strip().lower()
            user.student_id = student_id.strip()
            user.username = student_id.strip()
            user.grade_level = grade_level
            user.section = section

            self._log_audit(
                session,
                "Voter updated",
                f"Voter updated: {user.full_name} ({user.student_id})",
                user.user_id,
            )
            
            session.commit()
            return True, "Voter updated successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Update failed: {str(e)}"
        finally:
            session.close()
    
    def delete_voter(self, user_id: int) -> tuple[bool, str]:
        """Delete a voter."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False, "User not found."
            self._log_audit(
                session,
                "Voter deleted",
                f"Voter deleted: {user.full_name} ({user.student_id})",
                user.user_id,
            )
            session.delete(user)
            session.commit()
            return True, "Voter deleted successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Delete failed: {str(e)}"
        finally:
            session.close()
    
    # === Election methods ===
    def get_active_election(self) -> dict | None:
        """Get the currently active election."""
        session = get_session()
        try:
            elections = session.query(Election).all()
            self._sync_election_statuses(session, elections)
            election = session.query(Election).filter(Election.status == 'active').first()
            return election.to_dict() if election else None
        finally:
            session.close()
    
    def get_election_by_id(self, election_id: int) -> dict | None:
        """Get election by ID."""
        session = get_session()
        try:
            election = session.query(Election).filter(Election.election_id == election_id).first()
            if election:
                self._sync_election_statuses(session, [election])
            return election.to_dict() if election else None
        finally:
            session.close()
    
    def get_user_allowed_elections(self, user_id: int) -> list[dict]:
        """Get elections the user is allowed to participate in."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return []

            # Include all statuses so the student dashboard can show
            # upcoming/active/finalized elections in the tabs.
            elections = session.query(Election).order_by(Election.start_date.desc()).all()
            self._sync_election_statuses(session, elections)
            allowed = []
            for e in elections:
                if e.is_user_eligible(user):
                    allowed.append(e.to_dict())
            return allowed
        finally:
            session.close()
    
    def get_all_elections(self) -> list[dict]:
        """Get all elections."""
        session = get_session()
        try:
            elections = session.query(Election).order_by(Election.created_at.desc()).all()
            self._sync_election_statuses(session, elections)
            return [e.to_dict() for e in elections]
        finally:
            session.close()
    
    def create_election(self, title: str, description: str, start_date: str, end_date: str,
                        status: str = 'upcoming', allowed_grade=None, allowed_section='ALL') -> tuple[bool, str]:
        """Create a new election."""
        session = get_session()
        try:
            election = Election(
                title=title.strip(),
                description=description,
                start_date=start_date,
                end_date=end_date,
                status=status,
                allowed_grade=allowed_grade,
                allowed_section=allowed_section
            )
            session.add(election)
            self._log_audit(
                session,
                "Election created",
                f"Election created: {election.title}",
                None,
            )
            session.commit()
            return True, "Election created successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to create election: {str(e)}"
        finally:
            session.close()
    
    def update_election(self, election_id: int, title: str, description: str, start_date: str,
                        end_date: str, status: str, allowed_grade=None, allowed_section='ALL',
                        status_locked: bool | None = None) -> tuple[bool, str]:
        """Update an election."""
        session = get_session()
        try:
            election = session.query(Election).filter(Election.election_id == election_id).first()
            if not election:
                return False, "Election not found."
            
            election.title = title.strip()
            election.description = description
            election.start_date = start_date
            election.end_date = end_date
            election.status = status
            if status_locked is not None:
                election.status_locked = bool(status_locked)
            election.allowed_grade = allowed_grade
            election.allowed_section = allowed_section

            self._log_audit(
                session,
                "Election updated",
                f"Election updated: {election.title} (status: {election.status})",
                None,
            )
            
            session.commit()
            return True, "Election updated successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to update election: {str(e)}"
        finally:
            session.close()
    
    def delete_election(self, election_id: int) -> tuple[bool, str]:
        """Delete an election."""
        session = get_session()
        try:
            election = session.query(Election).filter(Election.election_id == election_id).first()
            if not election:
                return False, "Election not found."
            self._log_audit(
                session,
                "Election deleted",
                f"Election deleted: {election.title}",
                None,
            )
            session.delete(election)
            session.commit()
            return True, "Election deleted successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to delete election: {str(e)}"
        finally:
            session.close()
    
    def get_election_results(self, election_id: int = None) -> dict:
        """Get election results with candidate vote counts."""
        session = get_session()
        try:
            self._sync_all_elections(session)
            if election_id:
                election = session.query(Election).filter(Election.election_id == election_id).first()
            else:
                election = session.query(Election).filter(
                    Election.status.in_(['active', 'finalized'])
                ).order_by(Election.end_date.desc()).first()
            
            if not election:
                return {"election": None, "candidates": [], "total_votes": 0}
            
            candidates = session.query(Candidate).filter(
                Candidate.election_id == election.election_id
            ).order_by(Candidate.vote_count.desc()).all()
            
            total_votes = sum(c.vote_count for c in candidates)
            
            return {
                "election": election.to_dict(),
                "candidates": [c.to_dict() for c in candidates],
                "total_votes": total_votes
            }
        finally:
            session.close()
    
    def get_admin_stats(self) -> dict:
        """Get admin dashboard statistics."""
        session = get_session()
        try:
            self._sync_all_elections(session)
            total_voters = session.query(func.count(User.user_id)).filter(User.role == 'student').scalar() or 0
            votes_cast = session.query(func.count(VotingRecord.record_id)).scalar() or 0
            participating_voters = session.query(func.count(func.distinct(VotingRecord.user_id)))\
                .join(User, User.user_id == VotingRecord.user_id)\
                .filter(User.role == 'student').scalar() or 0
            active_elections = session.query(func.count(Election.election_id)).filter(
                Election.status == 'active'
            ).scalar() or 0
            
            participation_rate = round((participating_voters / total_voters * 100), 1) if total_voters > 0 else 0
            
            return {
                "total_voters": total_voters,
                "votes_cast": votes_cast,
                "participation_rate": participation_rate,
                "active_elections": active_elections
            }
        finally:
            session.close()
    
    def get_recent_activity(self, limit: int | None = 5) -> list[dict]:
        """Get recent audit activity (fallback for dashboards)."""
        return self.get_audit_logs(limit)
    
    def get_dashboard_chart_data(self, mode: str = "results") -> dict:
        """Get chart data for admin dashboard.

        Modes:
        - results: candidate vote counts for the active/most recent election
        - position_turnout: participation count per position in a ballot election
        - grade_section_turnout: turnout percentage per grade or section (based on election restrictions)
        """
        session = get_session()
        try:
            self._sync_all_elections(session)
            chart_mode = (mode or "results").strip().lower()

            # Select a target election.
            election = session.query(Election).filter(Election.status == 'active').order_by(
                Election.start_date.desc()
            ).first()

            if not election:
                if chart_mode == "position_turnout":
                    election = session.query(Election).filter(
                        Election.positions.any()
                    ).order_by(Election.end_date.desc()).first()
                else:
                    election = session.query(Election).filter(
                        Election.candidates.any()
                    ).order_by(Election.end_date.desc()).first()

            if not election:
                return {"title": "Dashboard", "data": []}

            if chart_mode == "position_turnout":
                positions = session.query(Position).filter(
                    Position.election_id == election.election_id
                ).order_by(Position.display_order).all()

                if not positions:
                    return {"title": f"Turnout by Position: {election.title}", "data": []}

                counts = dict(
                    session.query(
                        VotingRecord.position_id,
                        func.count(VotingRecord.record_id)
                    ).filter(
                        VotingRecord.election_id == election.election_id,
                        VotingRecord.position_id.isnot(None)
                    ).group_by(VotingRecord.position_id).all()
                )

                chart_data = [(p.title, int(counts.get(p.position_id, 0))) for p in positions]
                return {"title": f"Turnout by Position: {election.title}", "data": chart_data}

            if chart_mode == "grade_section_turnout":
                # Turnout is measured as distinct users who participated in the election
                # (cast or spoiled records count as participation).
                allowed_grade = election.allowed_grade
                allowed_section = (election.allowed_section or "").strip()

                user_filters = []
                if allowed_grade is not None:
                    user_filters.append(User.grade_level == allowed_grade)
                if allowed_section and allowed_section.upper() != "ALL":
                    user_filters.append(func.upper(User.section) == allowed_section.upper())

                # Choose breakdown: per-section when election is grade-restricted; otherwise per-grade.
                breakdown = "grade"
                if allowed_grade is not None:
                    breakdown = "section"
                if allowed_section and allowed_section.upper() != "ALL":
                    breakdown = "section"

                if breakdown == "section":
                    totals = dict(
                        session.query(User.section, func.count(User.user_id))
                        .filter(User.role == 'student', *user_filters)
                        .group_by(User.section)
                        .all()
                    )

                    voters = dict(
                        session.query(User.section, func.count(func.distinct(VotingRecord.user_id)))
                        .join(VotingRecord, VotingRecord.user_id == User.user_id)
                        .filter(
                            VotingRecord.election_id == election.election_id,
                            User.role == 'student',
                            *user_filters
                        )
                        .group_by(User.section)
                        .all()
                    )

                    data = []
                    for section, total in totals.items():
                        total_int = int(total or 0)
                        voted_int = int(voters.get(section, 0) or 0)
                        pct = int(round((voted_int / total_int) * 100)) if total_int > 0 else 0
                        label = (section or "Unknown").strip() or "Unknown"
                        data.append((label, pct))

                    data.sort(key=lambda x: x[0].lower())
                    return {"title": f"Turnout by Section (%): {election.title}", "data": data}

                totals = dict(
                    session.query(User.grade_level, func.count(User.user_id))
                    .filter(User.role == 'student', *user_filters)
                    .group_by(User.grade_level)
                    .all()
                )

                voters = dict(
                    session.query(User.grade_level, func.count(func.distinct(VotingRecord.user_id)))
                    .join(VotingRecord, VotingRecord.user_id == User.user_id)
                    .filter(
                        VotingRecord.election_id == election.election_id,
                        User.role == 'student',
                        *user_filters
                    )
                    .group_by(User.grade_level)
                    .all()
                )

                data = []
                for grade, total in totals.items():
                    total_int = int(total or 0)
                    voted_int = int(voters.get(grade, 0) or 0)
                    pct = int(round((voted_int / total_int) * 100)) if total_int > 0 else 0
                    label = f"Grade {grade}" if grade is not None else "Unknown"
                    data.append((label, pct))

                data.sort(key=lambda x: ("999" if x[0] == "Unknown" else x[0]))
                return {"title": f"Turnout by Grade (%): {election.title}", "data": data}

            # Default: live results
            # IMPORTANT: Do not chart every candidate (can be hundreds, bars become unreadable).
            # Instead, chart the current leader per position (one bar per position).
            candidates = session.query(Candidate).filter(
                Candidate.election_id == election.election_id
            ).all()

            vote_counts = dict(
                session.query(VotingRecord.candidate_id, func.count(VotingRecord.record_id))
                .filter(
                    VotingRecord.election_id == election.election_id,
                    VotingRecord.candidate_id.isnot(None),
                    VotingRecord.status == 'cast'
                )
                .group_by(VotingRecord.candidate_id)
                .all()
            )

            # Group candidates by position and pick the leader per position.
            cands_by_pos: dict[int | None, list[Candidate]] = {}
            for c in candidates:
                cands_by_pos.setdefault(c.position_id, []).append(c)

            positions = session.query(Position).filter(
                Position.election_id == election.election_id
            ).order_by(Position.display_order).all()

            chart_data: list[tuple[str, int]] = []
            if positions:
                for p in positions:
                    group = cands_by_pos.get(p.position_id) or []
                    if not group:
                        chart_data.append((p.title, 0))
                        continue

                    def _cand_votes(cand: Candidate) -> int:
                        count = vote_counts.get(cand.candidate_id)
                        if count is None:
                            count = cand.vote_count or 0
                        return int(count)

                    leader = max(group, key=_cand_votes)
                    chart_data.append((p.title, _cand_votes(leader)))

                # Include "General" bucket for candidates without a position.
                unassigned = cands_by_pos.get(None) or []
                if unassigned:
                    def _cand_votes(cand: Candidate) -> int:
                        count = vote_counts.get(cand.candidate_id)
                        if count is None:
                            count = cand.vote_count or 0
                        return int(count)

                    leader = max(unassigned, key=_cand_votes)
                    chart_data.append(("General", _cand_votes(leader)))

                return {"title": f"Live Results by Position: {election.title}", "data": chart_data}

            # Fallback: if the election has no positions configured, show only the top N candidates.
            fallback = []
            for c in candidates:
                count = vote_counts.get(c.candidate_id)
                if count is None:
                    count = c.vote_count or 0
                fallback.append((c.full_name, int(count)))
            fallback.sort(key=lambda x: x[1], reverse=True)
            fallback = fallback[:10]
            return {"title": f"Live Results (Top 10): {election.title}", "data": fallback}
        finally:
            session.close()

    def get_election_chart_data(self, election_id: int, mode: str = "results") -> dict:
        """Get chart data for a specific election.

        This mirrors `get_dashboard_chart_data` but allows the caller to choose the election.
        """
        session = get_session()
        try:
            chart_mode = (mode or "results").strip().lower()
            election = session.query(Election).filter(Election.election_id == election_id).first()
            if not election:
                return {"title": "Dashboard", "data": []}

            if chart_mode == "position_turnout":
                positions = session.query(Position).filter(
                    Position.election_id == election.election_id
                ).order_by(Position.display_order).all()

                if not positions:
                    return {"title": f"Turnout by Position: {election.title}", "data": []}

                counts = dict(
                    session.query(
                        VotingRecord.position_id,
                        func.count(VotingRecord.record_id)
                    ).filter(
                        VotingRecord.election_id == election.election_id,
                        VotingRecord.position_id.isnot(None)
                    ).group_by(VotingRecord.position_id).all()
                )

                chart_data = [(p.title, int(counts.get(p.position_id, 0))) for p in positions]
                return {"title": f"Turnout by Position: {election.title}", "data": chart_data}

            if chart_mode == "grade_section_turnout":
                allowed_grade = election.allowed_grade
                allowed_section = (election.allowed_section or "").strip()

                user_filters = []
                if allowed_grade is not None:
                    user_filters.append(User.grade_level == allowed_grade)
                if allowed_section and allowed_section.upper() != "ALL":
                    user_filters.append(func.upper(User.section) == allowed_section.upper())

                breakdown = "grade"
                if allowed_grade is not None:
                    breakdown = "section"
                if allowed_section and allowed_section.upper() != "ALL":
                    breakdown = "section"

                if breakdown == "section":
                    totals = dict(
                        session.query(User.section, func.count(User.user_id))
                        .filter(User.role == 'student', *user_filters)
                        .group_by(User.section)
                        .all()
                    )

                    voters = dict(
                        session.query(User.section, func.count(func.distinct(VotingRecord.user_id)))
                        .join(VotingRecord, VotingRecord.user_id == User.user_id)
                        .filter(
                            VotingRecord.election_id == election.election_id,
                            User.role == 'student',
                            *user_filters
                        )
                        .group_by(User.section)
                        .all()
                    )

                    data = []
                    for section, total in totals.items():
                        total_int = int(total or 0)
                        voted_int = int(voters.get(section, 0) or 0)
                        pct = int(round((voted_int / total_int) * 100)) if total_int > 0 else 0
                        label = (section or "Unknown").strip() or "Unknown"
                        data.append((label, pct))

                    data.sort(key=lambda x: x[0].lower())
                    return {"title": f"Turnout by Section (%): {election.title}", "data": data}

                totals = dict(
                    session.query(User.grade_level, func.count(User.user_id))
                    .filter(User.role == 'student', *user_filters)
                    .group_by(User.grade_level)
                    .all()
                )

                voters = dict(
                    session.query(User.grade_level, func.count(func.distinct(VotingRecord.user_id)))
                    .join(VotingRecord, VotingRecord.user_id == User.user_id)
                    .filter(
                        VotingRecord.election_id == election.election_id,
                        User.role == 'student',
                        *user_filters
                    )
                    .group_by(User.grade_level)
                    .all()
                )

                data = []
                for grade, total in totals.items():
                    total_int = int(total or 0)
                    voted_int = int(voters.get(grade, 0) or 0)
                    pct = int(round((voted_int / total_int) * 100)) if total_int > 0 else 0
                    label = f"Grade {grade}" if grade is not None else "Unknown"
                    data.append((label, pct))

                data.sort(key=lambda x: ("999" if x[0] == "Unknown" else x[0]))
                return {"title": f"Turnout by Grade (%): {election.title}", "data": data}

            # Default: live results
            # IMPORTANT: Do not chart every candidate (can be hundreds, bars become unreadable).
            # Instead, chart the current leader per position (one bar per position).
            candidates = session.query(Candidate).filter(
                Candidate.election_id == election.election_id
            ).all()

            vote_counts = dict(
                session.query(VotingRecord.candidate_id, func.count(VotingRecord.record_id))
                .filter(
                    VotingRecord.election_id == election.election_id,
                    VotingRecord.candidate_id.isnot(None),
                    VotingRecord.status == 'cast'
                )
                .group_by(VotingRecord.candidate_id)
                .all()
            )

            cands_by_pos: dict[int | None, list[Candidate]] = {}
            for c in candidates:
                cands_by_pos.setdefault(c.position_id, []).append(c)

            positions = session.query(Position).filter(
                Position.election_id == election.election_id
            ).order_by(Position.display_order).all()

            chart_data: list[tuple[str, int]] = []
            if positions:
                for p in positions:
                    group = cands_by_pos.get(p.position_id) or []
                    if not group:
                        chart_data.append((p.title, 0))
                        continue

                    def _cand_votes(cand: Candidate) -> int:
                        count = vote_counts.get(cand.candidate_id)
                        if count is None:
                            count = cand.vote_count or 0
                        return int(count)

                    leader = max(group, key=_cand_votes)
                    chart_data.append((p.title, _cand_votes(leader)))

                unassigned = cands_by_pos.get(None) or []
                if unassigned:
                    def _cand_votes(cand: Candidate) -> int:
                        count = vote_counts.get(cand.candidate_id)
                        if count is None:
                            count = cand.vote_count or 0
                        return int(count)

                    leader = max(unassigned, key=_cand_votes)
                    chart_data.append(("General", _cand_votes(leader)))

                return {"title": f"Live Results by Position: {election.title}", "data": chart_data}

            fallback = []
            for c in candidates:
                count = vote_counts.get(c.candidate_id)
                if count is None:
                    count = c.vote_count or 0
                fallback.append((c.full_name, int(count)))
            fallback.sort(key=lambda x: x[1], reverse=True)
            fallback = fallback[:10]
            return {"title": f"Live Results (Top 10): {election.title}", "data": fallback}
        finally:
            session.close()
    
    # === Candidate methods ===
    def get_candidates_for_election(self, election_id: int) -> list[dict]:
        """Get all candidates for a specific election."""
        session = get_session()
        try:
            candidates = session.query(Candidate).filter(
                Candidate.election_id == election_id
            ).order_by(Candidate.full_name).all()
            return [c.to_dict() for c in candidates]
        finally:
            session.close()
    
    def get_all_candidates(self) -> list[dict]:
        """Get all candidates with election info."""
        session = get_session()
        try:
            candidates = session.query(Candidate).join(Election).all()
            result = []
            for c in candidates:
                cand_dict = c.to_dict()
                cand_dict['election_title'] = c.election.title
                result.append(cand_dict)
            return result
        finally:
            session.close()
    
    def create_candidate(self, election_id: int, full_name: str, slogan: str,
                         photo_path: str = None) -> tuple[bool, str]:
        """Create a new candidate."""
        session = get_session()
        try:
            candidate = Candidate(
                election_id=election_id,
                full_name=full_name.strip(),
                slogan=slogan,
                photo_path=photo_path,
                vote_count=0
            )
            session.add(candidate)
            self._log_audit(
                session,
                "Candidate created",
                f"Candidate created: {candidate.full_name} (election_id: {election_id})",
                None,
            )
            session.commit()
            return True, "Candidate created successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to create candidate: {str(e)}"
        finally:
            session.close()
    
    def update_candidate(self, candidate_id: int, full_name: str, slogan: str,
                         photo_path: str = None, election_id: int = None) -> tuple[bool, str]:
        """Update a candidate."""
        session = get_session()
        try:
            candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
            if not candidate:
                return False, "Candidate not found."
            
            candidate.full_name = full_name.strip()
            candidate.slogan = slogan
            if photo_path:
                candidate.photo_path = photo_path
            if election_id:
                candidate.election_id = election_id

            self._log_audit(
                session,
                "Candidate updated",
                f"Candidate updated: {candidate.full_name} (id: {candidate.candidate_id})",
                None,
            )
            
            session.commit()
            return True, "Candidate updated successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to update candidate: {str(e)}"
        finally:
            session.close()
    
    def delete_candidate(self, candidate_id: int) -> tuple[bool, str]:
        """Delete a candidate."""
        session = get_session()
        try:
            candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
            if not candidate:
                return False, "Candidate not found."
            self._log_audit(
                session,
                "Candidate deleted",
                f"Candidate deleted: {candidate.full_name} (id: {candidate.candidate_id})",
                None,
            )
            session.delete(candidate)
            session.commit()
            return True, "Candidate deleted successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to delete candidate: {str(e)}"
        finally:
            session.close()
    
    # === Section methods ===
    def get_sections(self) -> list[dict]:
        """Get all sections."""
        session = get_session()
        try:
            sections = session.query(Section).order_by(Section.grade_level, Section.section_name).all()
            return [s.to_dict() for s in sections]
        finally:
            session.close()
    
    def create_section(self, grade_level: int, section_name: str) -> tuple[bool, str]:
        """Create a new section."""
        session = get_session()
        try:
            section = Section(grade_level=grade_level, section_name=section_name.strip())
            session.add(section)
            session.commit()
            return True, "Section created successfully!"
        except IntegrityError:
            session.rollback()
            return False, "Section already exists."
        except Exception as e:
            session.rollback()
            return False, f"Failed to create section: {str(e)}"
        finally:
            session.close()
    
    # === Voting record methods ===
    def has_user_voted(self, user_id: int, election_id: int) -> bool:
        """Check if user has already voted in an election."""
        session = get_session()
        try:
            record = session.query(VotingRecord).filter(
                and_(VotingRecord.user_id == user_id, VotingRecord.election_id == election_id)
            ).first()
            return record is not None
        finally:
            session.close()
    
    def get_user_voting_history(self, user_id: int) -> list[dict]:
        """Get voting history for a user."""
        session = get_session()
        try:
            records = session.query(VotingRecord).filter(
                VotingRecord.user_id == user_id
            ).join(Election).order_by(VotingRecord.voted_at.desc()).all()
            
            result = []
            for r in records:
                candidate_name = None
                if r.candidate:
                    candidate_name = r.candidate.full_name
                
                result.append({
                    'record_id': r.record_id,
                    'election_id': r.election_id,
                    'election_title': r.election.title,
                    'candidate_name': candidate_name,
                    'voted_at': r.voted_at,
                    'status': r.status
                })
            return result
        finally:
            session.close()
    
    def cast_vote(self, user_id: int, election_id: int, candidate_id: int) -> tuple[bool, str]:
        """Cast a vote for a candidate (legacy single-vote method)."""
        session = get_session()
        try:
            candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
            if not candidate:
                return False, "Candidate not found."

            # Vote is tracked per position (preferred). If position is missing, fall back to election-level.
            position_id = candidate.position_id
            if position_id is not None:
                existing = session.query(VotingRecord).filter(
                    and_(
                        VotingRecord.user_id == user_id,
                        VotingRecord.election_id == election_id,
                        VotingRecord.position_id == position_id,
                    )
                ).first()
                if existing:
                    return False, "You have already voted for this position in this election."
            else:
                existing = session.query(VotingRecord).filter(
                    and_(VotingRecord.user_id == user_id, VotingRecord.election_id == election_id)
                ).first()
                if existing:
                    return False, "You have already voted in this election."
            
            # Create voting record
            record = VotingRecord(
                user_id=user_id,
                election_id=election_id,
                position_id=position_id,
                candidate_id=candidate_id,
                status='cast'
            )
            session.add(record)
            
            # Update candidate vote count
            candidate.vote_count = (candidate.vote_count or 0) + 1

            self._log_audit(
                session,
                "Vote cast",
                f"Vote cast for {candidate.full_name} (election_id: {election_id})",
                user_id,
            )
            
            session.commit()
            return True, "Vote cast successfully!"
        except IntegrityError:
            session.rollback()
            # Most commonly triggered by the unique index on (user_id, election_id, position_id)
            return False, "You have already voted for this position in this election."
        except Exception as e:
            session.rollback()
            return False, f"Failed to cast vote: {str(e)}"
        finally:
            session.close()
    
    # === Position methods ===
    def get_positions_for_election(self, election_id: int) -> list[dict]:
        """Get all positions for an election, ordered by display_order."""
        session = get_session()
        try:
            positions = session.query(Position).filter(
                Position.election_id == election_id
            ).order_by(Position.display_order).all()
            return [p.to_dict() for p in positions]
        finally:
            session.close()
    
    def create_position(self, election_id: int, title: str, display_order: int = 0) -> tuple[bool, str, int | None]:
        """Create a new position for an election."""
        session = get_session()
        try:
            position = Position(
                election_id=election_id,
                title=title.strip(),
                display_order=display_order
            )
            session.add(position)
            self._log_audit(
                session,
                "Position created",
                f"Position created: {position.title} (election_id: {election_id})",
                None,
            )
            session.commit()
            position_id = position.position_id
            return True, "Position created successfully!", position_id
        except Exception as e:
            session.rollback()
            return False, f"Failed to create position: {str(e)}", None
        finally:
            session.close()
    
    def update_position(self, position_id: int, title: str, display_order: int = None) -> tuple[bool, str]:
        """Update a position."""
        session = get_session()
        try:
            position = session.query(Position).filter(Position.position_id == position_id).first()
            if not position:
                return False, "Position not found."
            position.title = title.strip()
            if display_order is not None:
                position.display_order = display_order
            self._log_audit(
                session,
                "Position updated",
                f"Position updated: {position.title} (id: {position.position_id})",
                None,
            )
            session.commit()
            return True, "Position updated successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to update position: {str(e)}"
        finally:
            session.close()
    
    def delete_position(self, position_id: int) -> tuple[bool, str]:
        """Delete a position."""
        session = get_session()
        try:
            position = session.query(Position).filter(Position.position_id == position_id).first()
            if not position:
                return False, "Position not found."
            self._log_audit(
                session,
                "Position deleted",
                f"Position deleted: {position.title} (id: {position.position_id})",
                None,
            )
            session.delete(position)
            session.commit()
            return True, "Position deleted successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to delete position: {str(e)}"
        finally:
            session.close()
    
    def get_candidates_by_position(self, position_id: int) -> list[dict]:
        """Get candidates for a specific position."""
        session = get_session()
        try:
            candidates = session.query(Candidate).filter(
                Candidate.position_id == position_id
            ).order_by(Candidate.full_name).all()
            return [c.to_dict() for c in candidates]
        finally:
            session.close()
    
    def assign_candidate_to_position(self, candidate_id: int, position_id: int) -> tuple[bool, str]:
        """Assign a candidate to a position."""
        session = get_session()
        try:
            candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
            if not candidate:
                return False, "Candidate not found."
            
            position = session.query(Position).filter(Position.position_id == position_id).first()
            if not position:
                return False, "Position not found."
            
            candidate.position_id = position_id
            # Also update legacy position text
            candidate.position = position.title
            self._log_audit(
                session,
                "Candidate assigned",
                f"Candidate assigned: {candidate.full_name} → {position.title}",
                None,
            )
            session.commit()
            return True, "Candidate assigned to position successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to assign candidate: {str(e)}"
        finally:
            session.close()
    
    def get_election_ballot_data(self, election_id: int) -> dict:
        """Get complete ballot data for an election (positions with candidates)."""
        session = get_session()
        try:
            election = session.query(Election).filter(Election.election_id == election_id).first()
            if not election:
                return {"election": None, "positions": []}
            
            positions = session.query(Position).filter(
                Position.election_id == election_id
            ).order_by(Position.display_order).all()
            
            ballot_data = {
                "election": election.to_dict(),
                "positions": []
            }
            
            for pos in positions:
                candidates = session.query(Candidate).filter(
                    Candidate.position_id == pos.position_id
                ).order_by(Candidate.full_name).all()
                
                ballot_data["positions"].append({
                    "position": pos.to_dict(),
                    "candidates": [c.to_dict() for c in candidates]
                })
            
            # Also include candidates without a position (legacy support)
            unassigned = session.query(Candidate).filter(
                and_(
                    Candidate.election_id == election_id,
                    Candidate.position_id.is_(None)
                )
            ).order_by(Candidate.full_name).all()
            
            if unassigned:
                ballot_data["positions"].append({
                    "position": {"position_id": None, "title": "General", "display_order": 999},
                    "candidates": [c.to_dict() for c in unassigned]
                })
            
            return ballot_data
        finally:
            session.close()
    
    def cast_ballot_votes(self, user_id: int, election_id: int, votes: list[dict]) -> tuple[bool, str]:
        """
        Cast votes for multiple positions in a single ballot.
        votes: list of {"position_id": int, "candidate_id": int}
        """
        session = get_session()
        try:
            # Allow partial ballots: only block duplicates per position.
            for vote in votes:
                position_id = vote.get("position_id")
                if position_id is None:
                    continue
                existing = session.query(VotingRecord).filter(
                    and_(
                        VotingRecord.user_id == user_id,
                        VotingRecord.election_id == election_id,
                        VotingRecord.position_id == position_id,
                    )
                ).first()
                if existing:
                    return False, "You have already voted for one or more positions in this election."
            
            # Create voting records for each position
            for vote in votes:
                position_id = vote.get("position_id")
                candidate_id = vote.get("candidate_id")

                status = 'cast' if candidate_id else 'spoiled'
                
                record = VotingRecord(
                    user_id=user_id,
                    election_id=election_id,
                    position_id=position_id,
                    candidate_id=candidate_id,
                    status=status
                )
                session.add(record)
                
                # Update candidate vote count
                if candidate_id and status == 'cast':
                    candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
                    if candidate:
                        candidate.vote_count = (candidate.vote_count or 0) + 1
            
            session.commit()
            return True, "Ballot submitted successfully!"
        except IntegrityError:
            session.rollback()
            return False, "You have already voted for one or more positions in this election."
        except Exception as e:
            session.rollback()
            return False, f"Failed to submit ballot: {str(e)}"
        finally:
            session.close()
    
    def has_user_voted_position(self, user_id: int, election_id: int, position_id: int) -> bool:
        """Check if user has voted for a specific position."""
        session = get_session()
        try:
            record = session.query(VotingRecord).filter(
                and_(
                    VotingRecord.user_id == user_id,
                    VotingRecord.election_id == election_id,
                    VotingRecord.position_id == position_id
                )
            ).first()
            return record is not None
        finally:
            session.close()
    
    def get_user_ballot_status(self, user_id: int, election_id: int) -> dict:
        """Get user's voting status for all positions in an election."""
        session = get_session()
        try:
            # Get all positions for the election
            positions = session.query(Position).filter(
                Position.election_id == election_id
            ).order_by(Position.display_order).all()
            
            # Get user's votes
            user_votes = session.query(VotingRecord).filter(
                and_(
                    VotingRecord.user_id == user_id,
                    VotingRecord.election_id == election_id
                )
            ).all()
            
            voted_positions = {v.position_id for v in user_votes}
            total_positions = len(positions)
            voted_count = len([p for p in positions if p.position_id in voted_positions])
            
            return {
                "total_positions": total_positions,
                "voted_count": voted_count,
                "completed": voted_count == total_positions and total_positions > 0,
                "voted_position_ids": list(voted_positions)
            }
        finally:
            session.close()
    
    def get_election_results_by_position(self, election_id: int) -> dict:
        """Get election results grouped by position."""
        session = get_session()
        try:
            election = session.query(Election).filter(Election.election_id == election_id).first()
            if not election:
                return {"election": None, "positions": [], "total_votes": 0}

            # Authoritative vote counts from voting_records (casts only), with legacy fallback.
            vote_counts = dict(
                session.query(VotingRecord.candidate_id, func.count(VotingRecord.record_id))
                .filter(
                    VotingRecord.election_id == election_id,
                    VotingRecord.candidate_id.isnot(None),
                    VotingRecord.status == 'cast'
                )
                .group_by(VotingRecord.candidate_id)
                .all()
            )
            
            positions = session.query(Position).filter(
                Position.election_id == election_id
            ).order_by(Position.display_order).all()
            
            results = {
                "election": election.to_dict(),
                "positions": [],
                "total_votes": 0
            }
            
            for pos in positions:
                candidates = session.query(Candidate).filter(
                    Candidate.position_id == pos.position_id
                ).all()

                candidate_dicts = []
                for c in candidates:
                    votes = vote_counts.get(c.candidate_id)
                    if votes is None:
                        votes = c.vote_count or 0
                    d = c.to_dict()
                    d['vote_count'] = int(votes)
                    candidate_dicts.append(d)

                candidate_dicts.sort(key=lambda x: int(x.get('vote_count') or 0), reverse=True)

                position_total = sum(int(c.get('vote_count') or 0) for c in candidate_dicts)
                results["total_votes"] += position_total

                winner = candidate_dicts[0] if candidate_dicts and int(candidate_dicts[0].get('vote_count') or 0) > 0 else None
                
                results["positions"].append({
                    "position": pos.to_dict(),
                    "candidates": candidate_dicts,
                    "total_votes": position_total,
                    "winner": winner if winner else None
                })
            
            # Handle unassigned candidates (legacy)
            unassigned = session.query(Candidate).filter(
                and_(
                    Candidate.election_id == election_id,
                    Candidate.position_id.is_(None)
                )
            ).all()
            
            if unassigned:
                candidate_dicts = []
                for c in unassigned:
                    votes = vote_counts.get(c.candidate_id)
                    if votes is None:
                        votes = c.vote_count or 0
                    d = c.to_dict()
                    d['vote_count'] = int(votes)
                    candidate_dicts.append(d)

                candidate_dicts.sort(key=lambda x: int(x.get('vote_count') or 0), reverse=True)

                position_total = sum(int(c.get('vote_count') or 0) for c in candidate_dicts)
                results["total_votes"] += position_total
                winner = candidate_dicts[0] if candidate_dicts and int(candidate_dicts[0].get('vote_count') or 0) > 0 else None
                results["positions"].append({
                    "position": {"position_id": None, "title": "General", "display_order": 999},
                    "candidates": candidate_dicts,
                    "total_votes": position_total,
                    "winner": winner if winner else None
                })
            
            return results
        finally:
            session.close()
    
    # Legacy method aliases
    def validate_login(self, username: str, student_id: str, password: str) -> tuple[bool, str]:
        """Legacy: Validate login credentials."""
        success, _ = self.authenticate_user(username, student_id, password)
        return (True, "Login successful!") if success else (False, "Invalid credentials.")
