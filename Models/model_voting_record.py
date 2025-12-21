"""
VotingRecord Model - SQLAlchemy ORM model for voting_records table.
"""
from sqlalchemy import Column, Integer, Enum, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Models.base import Base


class VotingRecord(Base):
    """VotingRecord ORM model - tracks user votes."""
    __tablename__ = 'voting_records'

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    election_id = Column(Integer, ForeignKey('elections.election_id', ondelete='CASCADE'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('candidates.candidate_id', ondelete='SET NULL'), nullable=True)
    status = Column(Enum('cast', 'spoiled'), default='cast')
    voted_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="votes")
    election = relationship("Election", back_populates="voting_records")
    candidate = relationship("Candidate", back_populates="votes")

    # Unique constraint - prevents duplicate votes per user per election
    __table_args__ = (
        UniqueConstraint('user_id', 'election_id', name='uniq_user_election'),
    )

    def __repr__(self):
        return f"<VotingRecord(record_id={self.record_id}, user_id={self.user_id}, election_id={self.election_id})>"

    def to_dict(self) -> dict:
        """Convert voting record to dictionary."""
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'election_id': self.election_id,
            'candidate_id': self.candidate_id,
            'status': self.status,
            'voted_at': self.voted_at
        }
