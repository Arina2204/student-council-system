from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.core.config import SECRET_KEY, ALGORITHM


router = APIRouter()
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None
        }
    )


@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()

    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Введите логин и пароль"
            }
        )

    user = db.query(User).filter(User.username == username).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Неверный логин"
            }
        )

    if not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Неверный пароль"
            }
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Пользователь отключён"
            }
        )

    access_token = create_access_token(
        {
            "sub": user.username,
            "role": user.role
        }
    )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax"
    )

    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


def get_token_from_request(
    request: Request,
    token: str | None = Depends(oauth2_scheme)
):
    if token:
        return token

    cookie_token = request.cookies.get("access_token")

    if not cookie_token:
        return None

    if cookie_token.startswith("Bearer "):
        return cookie_token.replace("Bearer ", "", 1)

    return cookie_token


def get_current_user(
    request: Request,
    token: str | None = Depends(get_token_from_request),
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь отключён")

    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
):
    cookie_token = request.cookies.get("access_token")

    if not cookie_token:
        return None

    if cookie_token.startswith("Bearer "):
        token = cookie_token.replace("Bearer ", "", 1)
    else:
        token = cookie_token

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        return None

    user = db.query(User).filter(User.username == username).first()

    if not user or not user.is_active:
        return None

    return user


def require_editor(current_user: User = Depends(get_current_user)):
    if current_user.role != "editor":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    return current_user