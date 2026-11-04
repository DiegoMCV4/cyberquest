from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..limiter import limiter
from ..models import User
from ..schemas import Credentials, TokenOut
from ..security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
@limiter.limit("10/hour")
def register(request: Request, data: Credentials, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(409, "Ese nombre de usuario ya existe")
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user.id))


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
def login(request: Request, data: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    # Mismo mensaje para usuario inexistente o contraseña errónea (evita enumerar usuarios)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    return TokenOut(access_token=create_token(user.id))


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "xp": user.xp,
        "level": user.xp // 100 + 1,
    }
