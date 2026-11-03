from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.engine import get_db
from app.models.club import Club
from app.schemas.club import ClubCreate, ClubResponse
from typing import List

router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.post("/", response_model=ClubResponse)
def create_club(
    club: ClubCreate,
    db: Session = Depends(get_db)
):
    new_club = Club(**club.model_dump())
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    return new_club


@router.get("/", response_model=List[ClubResponse])
def get_clubs(
    db: Session = Depends(get_db)
):
    return db.query(Club).all()