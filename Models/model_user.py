"""
User Model - SQLAlchemy ORM model for users table.
"""
import hashlib
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Models.base import Base


class User(Base):
    """User ORM model - represents students and admins."""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    student_id = Column(String(255), unique=True)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(Enum('student', 'admin'), default='student')
    grade_level = Column(Integer, default=None)
    section = Column(String(50), default=None)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    votes = relationship("VotingRecord", back_populates="user", cascade="all, delete-orphan")
    candidacies = relationship("Candidate", back_populates="user")

    # Indexes
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_student_id', 'student_id'),
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return self.password_hash == self.hash_password(password)

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
            'student_id': self.student_id,
            'email': self.email,
            'role': self.role,
            'grade_level': self.grade_level,
            'section': self.section,
            'created_at': self.created_at
        }
