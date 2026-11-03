from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database.engine import engine, get_db
from app.database.base import Base
from datetime import datetime

from app.models.student import Student
from app.models.student_club import StudentClub
from app.models.club_activity import ClubActivity
from app.models.organization import Organization

from app.routers import students, users, auth, activities
from collections import OrderedDict
from typing import Optional

from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from app.routers.auth import get_current_user_optional
from pydantic import BaseModel
from app.routers.auth import require_editor

app = FastAPI()

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

class OrganizationLeaderUpdate(BaseModel):
    leader_name: str
class OrganizationFieldUpdate(BaseModel):
    field: str
    value: str

class OrganizationCreateRequest(BaseModel):
    item_type: str
    name: str
    parent_id: Optional[int] = None
    leader_name: Optional[str] = ""
    faculty: Optional[str] = ""
    study_group: Optional[str] = ""
    contact_info: Optional[str] = ""

app.include_router(students.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(activities.router)

# -------------------------------------------------
# Функция получения дерева организаций
# -------------------------------------------------
def get_organization_tree(db: Session):
    roots = db.query(Organization).filter(Organization.parent_id == None).all()

    tree = []
    for root in roots:
        children = db.query(Organization).filter(
            Organization.parent_id == root.id
        ).all()

        tree.append({
            "root": root,
            "children": children
        })

    return tree


# -------------------------------------------------
# Главная страница
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):

    org_tree = get_organization_tree(db)

    sections = db.query(Organization).filter(Organization.parent_id == None).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "org_tree": org_tree,
            "current_user": current_user,
            "can_edit": current_user is not None and current_user.role == "editor"
        }
    )

# -------------------------------------------------
# Страница клуба
# -------------------------------------------------
@app.get("/club/{club_id}", response_class=HTMLResponse)
def club_page(club_id: int, request: Request, db: Session = Depends(get_db)):

    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "Клуб не найден"
            }
        )

    org_tree = get_organization_tree(db)

    activities_raw = (
        db.query(ClubActivity, Student)
        .join(Student, ClubActivity.student_id == Student.id)
        .filter(ClubActivity.club_id == club_id)
        .all()
    )

    activities_by_month = OrderedDict()
    activities_raw = sorted(activities_raw, key=lambda x: x[0].month)

    for activity, student in activities_raw:
        month = activity.month
        if month not in activities_by_month:
            activities_by_month[month] = []
        activities_by_month[month].append((activity, student))

    return templates.TemplateResponse(
        "club.html",
        {
            "request": request,
            "club": club,
            "org_tree": org_tree,
            "activities_by_month": activities_by_month
        }
    )


# -------------------------------------------------
# Проверка API
# -------------------------------------------------
@app.get("/api-status")
def api_status():
    try:
        connection = engine.connect()
        connection.close()
        return {"message": "Сервер работает и подключение к БД успешно"}
    except Exception as e:
        return {"message": str(e)}


@app.get("/organization/{org_id}", response_class=HTMLResponse)
def organization_page(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):

    # Получаем организацию
    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "Раздел не найден"
            }
        )

    # Получаем дерево организаций
    org_tree = get_organization_tree(db)

    # Получаем список верхних разделов для окна добавления объединения
    sections = db.query(Organization).filter(Organization.parent_id == None).all()

    # Получаем студентов + членство + возможную активность
    activities = (
        db.query(Student, StudentClub, ClubActivity)
        .join(StudentClub, Student.id == StudentClub.student_id)
        .outerjoin(
            ClubActivity,
            and_(
                Student.id == ClubActivity.student_id,
                ClubActivity.organization_id == org_id
            )
        )
        .filter(StudentClub.organization_id == org_id)
        .all()
    )

    other_members = (
        db.query(Organization, Student, StudentClub)
        .join(StudentClub, StudentClub.organization_id == Organization.id)
        .join(Student, Student.id == StudentClub.student_id)
        .filter(Organization.id != org_id)
        .filter(Organization.parent_id != None)
        .order_by(Student.last_name, Student.first_name, Organization.name)
        .all()
    )

    current_year = datetime.now().year

    months = [
        f"{current_year}-{month:02d}"
        for month in range(1, 13)
    ]

    return templates.TemplateResponse(
        "organization.html",
        {
            "request": request,
            "organization": org,
            "org_tree": org_tree,
            "sections": sections,
            "activities": activities,
            "months": months,
            "other_members": other_members,
            "current_user": current_user,
            "can_edit": current_user is not None and current_user.role == "editor"
        }
    )
@app.put("/organizations/{org_id}/leader")
def update_organization_leader(
    org_id: int,
    data: OrganizationLeaderUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_editor)
):
    organization = db.query(Organization).filter(Organization.id == org_id).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Объединение не найдено")

    leader_name = data.leader_name.strip()

    if not leader_name:
        raise HTTPException(
            status_code=400,
            detail="ФИО руководителя не может быть пустым"
        )

    organization.leader_name = leader_name

    db.commit()
    db.refresh(organization)

    return {
        "id": organization.id,
        "leader_name": organization.leader_name
    }
@app.put("/organizations/{org_id}/field")
def update_organization_field(
    org_id: int,
    data: OrganizationFieldUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_editor)
):
    organization = db.query(Organization).filter(Organization.id == org_id).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Объединение не найдено")

    allowed_fields = {
        "leader_name": "Руководитель",
        "faculty": "Факультет",
        "study_group": "Группа",
        "contact_info": "Контакты руководителя"
    }

    if data.field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Это поле нельзя редактировать")

    new_value = data.value.strip()

    if new_value == "":
        new_value = None

    setattr(organization, data.field, new_value)

    db.commit()
    db.refresh(organization)

    return {
        "id": organization.id,
        "field": data.field,
        "value": getattr(organization, data.field) or ""
    }
@app.post("/organizations/create")
def create_organization(
    data: OrganizationCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_editor)
):
    name = data.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Название не может быть пустым")

    if data.item_type not in ("section", "club"):
        raise HTTPException(status_code=400, detail="Некорректный тип элемента")

    if data.item_type == "club" and not data.parent_id:
        raise HTTPException(status_code=400, detail="Для объединения необходимо выбрать раздел")

    if data.item_type == "section":
        parent_id = None
        org_type = "section"
    else:
        parent_id = data.parent_id
        org_type = "club"

        parent = db.query(Organization).filter(Organization.id == parent_id).first()

        if not parent:
            raise HTTPException(status_code=404, detail="Выбранный раздел не найден")

    new_org = Organization(
        name=name,
        parent_id=parent_id,
        leader_name=(data.leader_name or "").strip() or None,
        faculty=(data.faculty or "").strip() or None,
        study_group=(data.study_group or "").strip() or None,
        contact_info=(data.contact_info or "").strip() or None,
        org_type=org_type
    )

    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    return {
        "success": True,
        "id": new_org.id,
        "name": new_org.name,
        "item_type": org_type
    }
@app.delete("/organizations/{org_id}")
def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_editor)
):
    organization = db.query(Organization).filter(Organization.id == org_id).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Раздел или объединение не найдено")

    children_count = db.query(Organization).filter(Organization.parent_id == org_id).count()

    if children_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить раздел, пока внутри него есть объединения. Сначала удалите объединения внутри раздела."
        )

    db.query(ClubActivity).filter(
        ClubActivity.organization_id == org_id
    ).delete(synchronize_session=False)

    db.query(StudentClub).filter(
        StudentClub.organization_id == org_id
    ).delete(synchronize_session=False)

    db.delete(organization)
    db.commit()

    return {
        "success": True,
        "message": "Элемент удалён"
    }