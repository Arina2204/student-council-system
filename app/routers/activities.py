from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.engine import get_db
from app.models.student import Student
from app.models.student_club import StudentClub
from app.models.club_activity import ClubActivity
from app.models.organization import Organization
from app.routers.auth import require_editor


router = APIRouter()


class ActivityData(BaseModel):
    organization_id: int
    month: str
    fio: str
    group_name: str
    role: str
    activity: str
    comment: Optional[str] = None
    row_color: Optional[str] = None


def normalize_row_color(value: Optional[str]):
    allowed_colors = {"green", "yellow", "red"}

    if value in allowed_colors:
        return value

    return None


def split_fio(fio: str):
    parts = fio.strip().split()

    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Введите ФИО минимум в формате: Фамилия Имя"
        )

    last_name = parts[0]
    first_name = parts[1]
    middle_name = " ".join(parts[2:]) if len(parts) > 2 else None

    return last_name, first_name, middle_name


@router.post("/activities")
def create_activity(
    data: ActivityData,
    db: Session = Depends(get_db),
    current_user=Depends(require_editor)
):
    organization = db.query(Organization).filter(
        Organization.id == data.organization_id
    ).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    last_name, first_name, middle_name = split_fio(data.fio)

    student = db.query(Student).filter(
        Student.last_name == last_name,
        Student.first_name == first_name,
        Student.middle_name == middle_name,
        Student.group_name == data.group_name
    ).first()

    if not student:
        student = Student(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            group_name=data.group_name
        )

        db.add(student)
        db.commit()
        db.refresh(student)

    membership = db.query(StudentClub).filter(
        StudentClub.student_id == student.id,
        StudentClub.organization_id == data.organization_id
    ).first()

    if membership:
        membership.role = data.role
    else:
        membership = StudentClub(
            student_id=student.id,
            organization_id=data.organization_id,
            role=data.role
        )

        db.add(membership)

    new_activity = ClubActivity(
        student_id=student.id,
        organization_id=data.organization_id,
        month=data.month,
        activity=data.activity,
        comment=data.comment,
        row_color=normalize_row_color(data.row_color)
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return {
        "message": "Запись добавлена",
        "id": new_activity.id
    }


@router.put("/activities/{activity_id}")
def update_activity(
    activity_id: int,
    data: ActivityData,
    db: Session = Depends(get_db),
    current_user=Depends(require_editor)
):
    activity = db.query(ClubActivity).filter(
        ClubActivity.id == activity_id
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    organization = db.query(Organization).filter(
        Organization.id == data.organization_id
    ).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    last_name, first_name, middle_name = split_fio(data.fio)

    student = db.query(Student).filter(
        Student.id == activity.student_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    student.last_name = last_name
    student.first_name = first_name
    student.middle_name = middle_name
    student.group_name = data.group_name

    membership = db.query(StudentClub).filter(
        StudentClub.student_id == student.id,
        StudentClub.organization_id == data.organization_id
    ).first()

    if membership:
        membership.role = data.role
    else:
        membership = StudentClub(
            student_id=student.id,
            organization_id=data.organization_id,
            role=data.role
        )

        db.add(membership)

    activity.organization_id = data.organization_id
    activity.month = data.month
    activity.activity = data.activity
    activity.comment = data.comment
    activity.row_color = normalize_row_color(data.row_color)

    db.commit()
    db.refresh(activity)

    return {
        "message": "Запись обновлена",
        "id": activity.id
    }


@router.delete("/activities/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_editor)
):
    activity = db.query(ClubActivity).filter(
        ClubActivity.id == activity_id
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    db.delete(activity)
    db.commit()

    return {
        "message": "Запись удалена"
    }