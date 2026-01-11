"""
Position Model - SQLAlchemy ORM model for positions table.
Positions represent roles within an election (e.g., President, Vice President, Secretary).
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Models.base import Base


class Position(Base):
    """Position ORM model - represents positions within an election."""
    __tablename__ = 'positions'

    position_id = Column(Integer, primary_key=True, autoincrement=True)
    election_id = Column(Integer, ForeignKey('elections.election_id', ondelete='CASCADE'), nullable=False)
    title = Column(String(128), nullable=False)  # e.g., "President", "Vice President"
    display_order = Column(Integer, default=0)  # For ordering positions in UI
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    election = relationship("Election", back_populates="positions")
    candidates = relationship("Candidate", back_populates="position_rel", cascade="all, delete-orphan")
    voting_records = relationship("VotingRecord", back_populates="position_rel")

    def __repr__(self):
        return f"<Position(position_id={self.position_id}, title='{self.title}', election_id={self.election_id})>"

    def to_dict(self) -> dict:
        """Convert position to dictionary."""
        return {
            'position_id': self.position_id,
            'election_id': self.election_id,
            'title': self.title,
            'display_order': self.display_order,
            'created_at': self.created_at
        }
