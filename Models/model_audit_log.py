"""
AuditLog Model - SQLAlchemy ORM model for audit_logs table.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from Models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    action = Column(String(128), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")

    def to_dict(self) -> dict:
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at,
        }
