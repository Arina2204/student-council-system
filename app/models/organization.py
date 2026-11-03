from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    leader_name = Column(String)
    faculty = Column(String)
    study_group = Column(String)
    contact_info = Column(String)
    org_type = Column(String(20))

    children = relationship("Organization")

    members = relationship(
        "StudentClub",
        back_populates="organization",
        cascade="all, delete"
    )

    activities = relationship(
        "ClubActivity",
        back_populates="organization",
        cascade="all, delete"
    )