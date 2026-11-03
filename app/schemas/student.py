from pydantic import BaseModel
from typing import Optional


class StudentCreate(BaseModel):
    last_name: str
    first_name: str
    group_name: str
    middle_name: Optional[str] = None
    status: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    last_name: str
    first_name: str
    group_name: str
    middle_name: Optional[str]
    status: Optional[str]

    class Config:
        from_attributes = True