"""
Section Model - SQLAlchemy ORM model for sections table.
"""
from sqlalchemy import Column, Integer, String, UniqueConstraint
from Models.base import Base


class Section(Base):
    """Section ORM model - represents grade sections."""
    __tablename__ = 'sections'

    section_id = Column(Integer, primary_key=True, autoincrement=True)
    grade_level = Column(Integer, nullable=False)
    section_name = Column(String(50), nullable=False)

    # Unique constraint on grade + section
    __table_args__ = (
        UniqueConstraint('grade_level', 'section_name', name='uniq_grade_section'),
    )

    def __repr__(self):
        return f"<Section(section_id={self.section_id}, grade={self.grade_level}, section='{self.section_name}')>"

    def to_dict(self) -> dict:
        """Convert section to dictionary."""
        return {
            'section_id': self.section_id,
            'grade_level': self.grade_level,
            'section_name': self.section_name
        }
