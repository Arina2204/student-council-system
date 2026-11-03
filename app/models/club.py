from sqlalchemy import Column, Integer, String
from app.database.base import Base
from sqlalchemy.orm import relationship


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    students = relationship(
        "StudentClub",
        back_populates="club",
        cascade="all, delete"
    )