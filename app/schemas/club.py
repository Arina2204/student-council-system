from pydantic import BaseModel
from typing import Optional


class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ClubResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True