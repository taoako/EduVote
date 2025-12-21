"""
Election Model - SQLAlchemy ORM model for elections table.
"""
from sqlalchemy import Column, Integer, String, Text, Enum, Date, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Models.base import Base


class Election(Base):
    """Election ORM model - represents voting elections."""
    __tablename__ = 'elections'

    election_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum('upcoming', 'active', 'finalized'), default='upcoming')
    start_date = Column(Date)
    end_date = Column(Date)
    allowed_grade = Column(Integer, default=None)  # 11, 12, or None for all
    allowed_section = Column(String(50), default='ALL')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    candidates = relationship("Candidate", back_populates="election", cascade="all, delete-orphan")
    voting_records = relationship("VotingRecord", back_populates="election", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Election(election_id={self.election_id}, title='{self.title}', status='{self.status}')>"

    def is_user_eligible(self, user) -> bool:
        """Check if a user is eligible to vote in this election."""
        # Grade rule: None means "all grades"
        if self.allowed_grade is not None:
            try:
                allowed_grade = int(self.allowed_grade)
            except (TypeError, ValueError):
                allowed_grade = None

            if allowed_grade is not None:
                try:
                    user_grade = int(user.grade_level) if user.grade_level is not None else None
                except (TypeError, ValueError):
                    user_grade = None

                if user_grade != allowed_grade:
                    return False

        # Section rule: 'ALL'/None/empty means "all sections"
        allowed_section = (self.allowed_section or "").strip()
        if allowed_section and allowed_section.upper() != "ALL":
            user_section = (getattr(user, "section", None) or "").strip()
            if user_section.upper() != allowed_section.upper():
                return False

        return True

    def to_dict(self) -> dict:
        """Convert election to dictionary."""
        return {
            'election_id': self.election_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'allowed_grade': self.allowed_grade,
            'allowed_section': self.allowed_section,
            'created_at': self.created_at
        }
