
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Models.base import Base


class Candidate(Base):
    """Candidate ORM model - represents election candidates."""
    __tablename__ = 'candidates'

    candidate_id = Column(Integer, primary_key=True, autoincrement=True)
    election_id = Column(Integer, ForeignKey('elections.election_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    full_name = Column(String(255), nullable=False)
    position = Column(String(128), nullable=True)
    slogan = Column(Text)
    photo_path = Column(String(512))
    vote_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    election = relationship("Election", back_populates="candidates")
    user = relationship("User", back_populates="candidacies")
    votes = relationship("VotingRecord", back_populates="candidate")

    def __repr__(self):
        return f"<Candidate(candidate_id={self.candidate_id}, full_name='{self.full_name}', votes={self.vote_count})>"

    def to_dict(self) -> dict:
        """Convert candidate to dictionary."""
        return {
            'candidate_id': self.candidate_id,
            'election_id': self.election_id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'position': self.position,
            'slogan': self.slogan,
            'photo_path': self.photo_path,
            'vote_count': self.vote_count,
            'created_at': self.created_at
        }
