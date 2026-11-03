from sqlalchemy import Column, Integer, String
from app.database.base import Base
from sqlalchemy.orm import relationship


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    status = Column(String, nullable=True)

    memberships = relationship(
        "StudentClub",
        back_populates="student",
        cascade="all, delete"
    )

    activities = relationship(
        "ClubActivity",
        back_populates="student",
        cascade="all, delete"
    )