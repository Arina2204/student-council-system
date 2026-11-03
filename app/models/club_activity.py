from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class ClubActivity(Base):
    __tablename__ = "club_activity"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    month = Column(Date, nullable=False)

    activity = Column(String, nullable=False)
    comment = Column(String, nullable=True)

    row_color = Column(String(20), nullable=True)

    student = relationship("Student")
    organization = relationship("Organization")