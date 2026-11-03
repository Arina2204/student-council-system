from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.student_club import StudentClub
from app.schemas.student import StudentCreate, StudentResponse
from app.database.engine import get_db
from typing import List
from app.routers.auth import require_editor

router = APIRouter()

@router.post("/students", response_model=StudentResponse)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_editor)
):

    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


@router.get("/students", response_model=List[StudentResponse])
def get_students(
    db: Session = Depends(get_db)
):
    students = db.query(Student).all()
    return students


# 👇 ВСТАВЛЯЕМ ЗДЕСЬ
@router.post("/students/{student_id}/join-club/{club_id}")
def join_club(
    student_id: int,
    club_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_editor)
):
    # Проверяем студента
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем клуб
    from app.models.club import Club
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")

    # Проверяем, не состоит ли уже
    existing = db.query(StudentClub).filter(
        StudentClub.student_id == student_id,
        StudentClub.club_id == club_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Студент уже состоит в этом клубе")

    membership = StudentClub(
        student_id=student_id,
        club_id=club_id
    )

    db.add(membership)
    db.commit()

    return {"message": "Студент успешно вступил в клуб"}

@router.get("/students/{student_id}/clubs")
def get_student_clubs(
    student_id: int,
    db: Session = Depends(get_db)
):
    from app.models.club import Club

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    memberships = db.query(StudentClub).filter(
        StudentClub.student_id == student_id
    ).all()

    club_ids = [m.club_id for m in memberships]

    clubs = db.query(Club).filter(Club.id.in_(club_ids)).all()

    return clubs

