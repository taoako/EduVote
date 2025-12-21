"""
Database Service Layer - provides business logic operations using SQLAlchemy ORM models.

THIS FILE IS THE SERVICE/REPOSITORY LAYER FOR CONTROLLERS.
It uses the SQLAlchemy ORM models:
    - Models.model_user.User
    - Models.model_election.Election
    - Models.model_candidate.Candidate
    - Models.model_section.Section
    - Models.model_voting_record.VotingRecord
"""
import hashlib
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError
from Models.base import get_session, init_db, get_connection
from Models.model_user import User
from Models.model_election import Election
from Models.model_candidate import Candidate
from Models.model_section import Section
from Models.model_voting_record import VotingRecord


class Database:
    """
    Service layer that provides data access operations using SQLAlchemy ORM.
    Controllers should use this class for all database operations.
    """
    
    def __init__(self):
        # Initialize database schema on first Database instance
        init_db()
    
    # === Connection methods (legacy support) ===
    def get_connection(self):
        """Legacy: Get raw MySQL connection for complex queries."""
        return get_connection()
    
    # === User methods ===
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
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
            password_hash = self.hash_password(password)
            user = session.query(User).filter(
                and_(
                    or_(User.username == username.strip(), User.student_id == student_id.strip()),
                    User.password_hash == password_hash
                )
            ).first()
            
            if user:
                return True, user.to_dict()
            return False, None
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
            election = session.query(Election).filter(Election.status == 'active').first()
            return election.to_dict() if election else None
        finally:
            session.close()
    
    def get_election_by_id(self, election_id: int) -> dict | None:
        """Get election by ID."""
        session = get_session()
        try:
            election = session.query(Election).filter(Election.election_id == election_id).first()
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
            session.commit()
            return True, "Election created successfully!"
        except Exception as e:
            session.rollback()
            return False, f"Failed to create election: {str(e)}"
        finally:
            session.close()
    
    def update_election(self, election_id: int, title: str, description: str, start_date: str,
                        end_date: str, status: str, allowed_grade=None, allowed_section='ALL') -> tuple[bool, str]:
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
            election.allowed_grade = allowed_grade
            election.allowed_section = allowed_section
            
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
            total_voters = session.query(func.count(User.user_id)).filter(User.role == 'student').scalar() or 0
            votes_cast = session.query(func.count(VotingRecord.record_id)).scalar() or 0
            active_elections = session.query(func.count(Election.election_id)).filter(
                Election.status == 'active'
            ).scalar() or 0
            
            participation_rate = round((votes_cast / total_voters * 100), 1) if total_voters > 0 else 0
            
            return {
                "total_voters": total_voters,
                "votes_cast": votes_cast,
                "participation_rate": participation_rate,
                "active_elections": active_elections
            }
        finally:
            session.close()
    
    def get_recent_activity(self, limit: int = 5) -> list[dict]:
        """Get recent voting activity."""
        session = get_session()
        try:
            records = session.query(VotingRecord).join(User).join(Election).order_by(
                VotingRecord.voted_at.desc()
            ).limit(limit).all()
            
            result = []
            for r in records:
                result.append({
                    'full_name': r.user.full_name,
                    'election_title': r.election.title,
                    'voted_at': r.voted_at
                })
            return result
        finally:
            session.close()
    
    def get_dashboard_chart_data(self) -> dict:
        """Get chart data for admin dashboard."""
        session = get_session()
        try:
            # Get active election or most recent
            election = session.query(Election).filter(Election.status == 'active').order_by(
                Election.start_date.desc()
            ).first()
            
            if not election:
                election = session.query(Election).filter(
                    Election.candidates.any()
                ).order_by(Election.end_date.desc()).first()
            
            if not election:
                return {"title": "Live Election Results", "data": []}
            
            candidates = session.query(Candidate).filter(
                Candidate.election_id == election.election_id
            ).order_by(Candidate.vote_count.desc()).all()
            
            chart_data = [(c.full_name, c.vote_count) for c in candidates]
            title = f"Live Election Results: {election.title}"
            
            return {"title": title, "data": chart_data}
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
        """Cast a vote for a candidate."""
        session = get_session()
        try:
            # Check if already voted
            existing = session.query(VotingRecord).filter(
                and_(VotingRecord.user_id == user_id, VotingRecord.election_id == election_id)
            ).first()
            if existing:
                return False, "You have already voted in this election."
            
            # Create voting record
            record = VotingRecord(
                user_id=user_id,
                election_id=election_id,
                candidate_id=candidate_id,
                status='cast'
            )
            session.add(record)
            
            # Update candidate vote count
            candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
            if candidate:
                candidate.vote_count = (candidate.vote_count or 0) + 1
            
            session.commit()
            return True, "Vote cast successfully!"
        except IntegrityError:
            session.rollback()
            return False, "You have already voted in this election."
        except Exception as e:
            session.rollback()
            return False, f"Failed to cast vote: {str(e)}"
        finally:
            session.close()
    
    # Legacy method aliases
    def validate_login(self, username: str, student_id: str, password: str) -> tuple[bool, str]:
        """Legacy: Validate login credentials."""
        success, _ = self.authenticate_user(username, student_id, password)
        return (True, "Login successful!") if success else (False, "Invalid credentials.")
