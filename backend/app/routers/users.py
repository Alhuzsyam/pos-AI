"""User management dalam satu tenant."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.user import User, UserRole
from app.core.deps import require_admin, require_manager, get_current_user, resolve_tenant_id
from app.core.security import hash_password

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "kasir"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


ALLOWED_ROLES = [r.value for r in UserRole if r != UserRole.SUPERADMIN]


def _user_dict(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "last_login": u.last_login,
        "created_at": u.created_at,
    }


@router.get("/", response_model=List[dict])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    q = db.query(User).filter(User.role != UserRole.SUPERADMIN)
    tid = resolve_tenant_id(current_user, db)
    q = q.filter(User.tenant_id == tid)
    return [_user_dict(u) for u in q.all()]


@router.post("/", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if body.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Role tidak valid. Pilihan: {ALLOWED_ROLES}")

    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username sudah dipakai")

    user = User(
        tenant_id=resolve_tenant_id(current_user, db),
        username=body.username,
        full_name=body.full_name or body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_dict(user)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tid,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if body.password:
        user.password_hash = hash_password(body.password)

    for field, value in body.model_dump(exclude_none=True, exclude={"password"}).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return _user_dict(user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Tidak bisa hapus diri sendiri")

    tid = resolve_tenant_id(current_user, db)
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tid,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    db.delete(user)
    db.commit()
