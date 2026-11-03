from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class StudentClub(Base):
    __tablename__ = "student_clubs"

    id = Column(Integer, primary_key=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    role = Column(String, default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    student = relationship("Student", back_populates="memberships")
    organization = relationship("Organization", back_populates="members")