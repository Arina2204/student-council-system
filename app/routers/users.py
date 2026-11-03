from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.engine import get_db
from app.models.user import User
from app.core.security import hash_password

router = APIRouter()

@router.post("/users")
def create_user(username: str, password: str, role: str = "viewer", db: Session = Depends(get_db)):
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    return {"message": "Пользователь создан"}